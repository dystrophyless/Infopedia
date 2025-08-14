import logging
from typing import Any, Awaitable, Callable
from psycopg_pool import AsyncConnectionPool

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update


logger = logging.getLogger(__name__)


class DatabaseMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any]
    ) -> Any:
        logger.debug("Входим в DatabaseMiddleware")

        db_pool: AsyncConnectionPool = data.get("db_pool")

        if db_pool is None:
            logging.error("Пул соединений не был предоставлен в данных мидлвари")
            raise RuntimeError("Отсутствует `db_pool` в контексте мидлвари")

        async with db_pool.connection() as connection:
            try:
                async with connection.transaction():
                    data["conn"] = connection
                    result = await handler(event, data)
            except Exception as e:
                logging.exception("Транзакция откатилась из-за следующей ошибки: %s", e)
                raise

        logger.debug("Выходим из DatabaseMiddleware")

        return result
