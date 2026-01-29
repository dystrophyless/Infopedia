import asyncio
import logging.config
import os
import sys

from sqlalchemy.exc import SQLAlchemyError

from database.connection import get_async_engine, init_vector_extension
from database.models import Base
from logs.logging_settings import logging_config
from config_data.config import Config, load_config


config: Config = load_config(".env")

logger = logging.getLogger(__name__)
logging.config.dictConfig(logging_config)

if sys.platform.startswith("win") or os.name == "nt":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def main():
    engine = None
    try:
        engine = get_async_engine(
            db_name=config.db.name,
            host=config.db.host,
            port=config.db.port,
            user=config.db.user,
            password=config.db.password,
        )

        await init_vector_extension(engine)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.debug(
            "Таблицы `users`, `user_feedback`, `activity`, `terms`, `sources`, `definitions`,  `feature_usage` были успешно созданы"
        )

    except SQLAlchemyError as db_error:
        logger.exception("Ошибка связанная с базой данных: %s", db_error)
    except Exception as e:
        logger.exception("Необработанная ошибка: %s", e)
    finally:
        if engine:
            await engine.dispose()
            logger.debug("Подключение к PostgreSQL было закрыто")


if __name__ == "__main__":
    asyncio.run(main())
