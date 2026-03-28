import asyncio
import logging.config
import os
import sys

from sqlalchemy.exc import SQLAlchemyError

from database.connection import init_vector_extension
from database.models import Base
from logs.logging_settings import logging_config

logger = logging.getLogger(__name__)
logging.config.dictConfig(logging_config)

if sys.platform.startswith("win") or os.name == "nt":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def create_tables(engine) -> None:
    try:
        await init_vector_extension(engine)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.debug(
            "Таблицы `users`, `user_feedback`, `activity`, `books`, `chapters`, "
            "`topic_codes`, `topics`, `terms`, `definitions`, `feature_usage` "
            "были успешно созданы",
        )

    except SQLAlchemyError as db_error:
        logger.exception("Ошибка связанная с базой данных: %s", db_error)
        raise
    except Exception as error:
        logger.exception("Необработанная ошибка: %s", error)
        raise
    finally:
        if engine:
            await engine.dispose()
            logger.debug("Подключение к PostgreSQL было закрыто")