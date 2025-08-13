import logging
from typing import Any, Awaitable, Callable
from psycopg import AsyncConnection

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update, User

from database.db import get_user, add_user_activity

logger = logging.getLogger(__name__)


class ActivityCounterMiddleware(BaseMiddleware):
    async def __call__(self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: dict[str, Any]
    ) -> Any:
        user: User = data.get("event_from_user")

        if user is None:
            return await handler(event, data)

        result = await handler(event, data)

        conn: AsyncConnection = data.get("conn")
        if conn is None:
            logger.error("Соединение с базой данных не было найдено в данных мидлвари")
            raise RuntimeError("Отстуствует соединение с базой данных для проверки теневого бана")

        row_user = await get_user(conn, user_id=user.id)

        if row_user is None:
            return result

        await add_user_activity(conn, user_id=user.id)

        return result