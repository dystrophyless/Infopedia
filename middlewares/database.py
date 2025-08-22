import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession



logger = logging.getLogger(__name__)


class DatabaseMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any]
    ) -> Any:
        logger.debug("Входим в DatabaseMiddleware")

        sessionmaker: async_sessionmaker[AsyncSession] = data.get("sessionmaker")

        if sessionmaker is None:
            logging.error("Пул соединений не был предоставлен в данных мидлвари")
            raise RuntimeError("Отсутствует `sessionmaker` в контексте мидлвари")

        async with sessionmaker() as session:
            try:
                async with session.begin():
                    data["session"] = session
                    result = await handler(event, data)
            except Exception as e:
                logger.exception("Транзакция откатилась из-за ошибки: %s", e)
                raise

        logger.debug("Выходим из DatabaseMiddleware")

        return result
