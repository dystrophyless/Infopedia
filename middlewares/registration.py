import logging
from typing import Any, Awaitable, Callable
from psycopg import AsyncConnection

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update, User
from aiogram.fsm.context import FSMContext

from fsm.states import FSMRegister
from enums.roles import UserRole
from database.db import get_user

logger = logging.getLogger(__name__)


class RegistrationMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: dict[str, Any]
    ) -> Any:
        user: User = data.get("event_from_user")

        if user is None:
            logger.warning("По какой-то неизвестной причине пользователя не удалось определить, переходим в следующий \"обработчик\"")
            return await handler(event, data)

        conn: AsyncConnection = data.get("conn")

        if conn is None:
            logger.error("Соединение с базой данных не было найдено в данных мидлвари")
            raise RuntimeError("Отстуствует соединение с базой данных для проверки теневого бана")

        user_row = await get_user(conn, user_id=user.id)

        if user_row is None:
            admin_ids: list[int] = data.get("admin_ids")
            if user.id in admin_ids:
                user_role = UserRole.ADMIN
            else:
                user_role = UserRole.USER

            state: FSMContext = data.get("state")
            user_context_data: dict = await state.get_data()

            user_context_data.update(user_role=user_role)
            await state.set_data(user_context_data)
            await state.set_state(FSMRegister.start_register)

        return await handler(event, data)

