import logging
from typing import Any, Awaitable, Callable
from psycopg import AsyncConnection

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update, User
from aiogram.fsm.context import FSMContext

from fsm.states import FSMMembership
from services.membership import is_user_followed
from database.db import get_user

logger = logging.getLogger(__name__)


class MembershipMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: dict[str, Any],
    ) -> Any:
        user: User = data.get("event_from_user")
        bot = data.get("bot")
        channel_id = data.get("channel_id")
        state: FSMContext = data.get("state")

        if not user or not state or not bot or not channel_id:
            return await handler(event, data)
        
        conn: AsyncConnection = data.get("conn")

        if conn is None:
            logger.error("Соединение с базой данных не было найдено в данных мидлвари")
            raise RuntimeError("Отстуствует соединение с базой данных для проверки теневого бана")


        row_user = await get_user(conn, user_id=user.id)

        if row_user is None:
            return await handler(event, data)

        is_following = await is_user_followed(bot, user.id, channel_id)

        if not is_following:
            await state.set_state(FSMMembership.await_membership)
            return

        return await handler(event, data)