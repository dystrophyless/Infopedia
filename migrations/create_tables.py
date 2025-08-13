import asyncio
import logging.config
import os
import sys
from psycopg import AsyncConnection, Error

from database.connection import get_pg_connection
from logs.logging_settings import logging_config
from config_data.config import Config, load_config

config: Config = load_config(".env")

logger = logging.getLogger(__name__)

logging.config.dictConfig(logging_config)

if sys.platform.startswith("win") or os.name == "nt":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def main():
    connection: AsyncConnection | None = None

    try:
        connection = await get_pg_connection(
            db_name=config.db.name,
            host=config.db.host,
            port=config.db.port,
            user=config.db.user,
            password=config.db.password
        )

        async with connection:
            async with connection.transaction():
                async with connection.cursor() as cursor:
                    await cursor.execute(
                        query="""
                            CREATE TABLE IF NOT EXISTS users(
                                id SERIAL PRIMARY KEY,
                                user_id BIGINT NOT NULL UNIQUE,
                                username VARCHAR(50),
                                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                                language VARCHAR(16) NOT NULL,
                                grade VARCHAR(16) NOT NULL,
                                role VARCHAR(32) NOT NULL,
                                is_alive BOOLEAN NOT NULL,
                                banned BOOLEAN NOT NULL
                            );
                        """
                    )
                    await cursor.execute(
                        query="""
                            CREATE TABLE IF NOT EXISTS activity(
                                id SERIAL PRIMARY KEY,
                                user_id BIGINT REFERENCES users(user_id),
                                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                                activity_date DATE NOT NULL DEFAULT CURRENT_DATE,
                                actions INT NOT NULL DEFAULT 1
                            );
                            CREATE UNIQUE INDEX IF NOT EXISTS idx_activity_user_day
                            ON activity (user_id, activity_date);
                        """
                    )
                    logger.debug("Таблицы `users` и `activiy` были успешно созданы")
    except Error as db_error:
        logger.exception("Ошибка связанная с базой данных: %s", db_error)
    except Exception as e:
        logger.exception("Необработанная ошибка: %s", e)
    finally:
        if connection:
            await connection.close()
            logger.debug("Подключение к PostgreSQL была закрыта")


asyncio.run(main())

