import logging
from typing import Any, Awaitable, Callable
from psycopg import AsyncConnection

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update, User
from database.db import get_user_banned_status_by_id


logger = logging.getLogger(__name__)


class ShadowBanMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: dict[str, Any]
    ) -> Any:
        user: User = data.get("event_from_user")

        if user is None:
            return await handler(event, data)

        conn: AsyncConnection = data.get("conn")

        if conn is None:
            logger.error("Соединение с базой данных не было найдено в данных мидлвари")
            raise RuntimeError("Отстуствует соединение с базой данных для проверки теневого бана")

        user_banned_status = await get_user_banned_status_by_id(conn, user_id=user.id)

        if user_banned_status:
            logger.warning("Забаненный пользователь с `user_id`='%d' попытался взаимодействовать с ботом", user.id)
            if event.callback_query:
                await event.callback_query.answer()
            return

        return await handler(event, data)