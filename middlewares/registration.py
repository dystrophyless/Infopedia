import logging
from typing import Any, Awaitable, Callable
from psycopg import AsyncConnection

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User
from aiogram.fsm.context import FSMContext

from fsm.states import FSMRegister
from enums.roles import UserRole
from database.db import get_user

logger = logging.getLogger(__name__)

class RegistrationMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any]
    ) -> Any:
        logger.debug("Входим в RegistrationMiddleware")

        user: User = data.get("event_from_user")

        if user is None:
            logger.warning("По какой-то неизвестной причине пользователя не удалось определить, переходим в следующий \"обработчик\"")
            return await handler(event, data)

        conn: AsyncConnection = data.get("conn")

        if conn is None:
            logger.error("Соединение с базой данных не было найдено в данных мидлвари")
            raise RuntimeError("Отстуствует соединение с базой данных для проверки теневого бана")

        username = user.username if user.username else user.first_name

        user_row = await get_user(conn, user_id=user.id)

        logger.debug("Строка о пользователе с `username`='%s': %s", username, user_row)

        state: FSMContext = data.get("state")

        if user_row is None:
            logger.debug("Данные о пользователе с `username`='%s' не удалось получить из базы данных, определяем роль пользователя, передаём в контекст, устанавливаем состояние регистрации, переходим в следующий \"обработчик\"", username)

            admin_ids: list[int] = data.get("admin_ids")
            if user.id in admin_ids:
                user_role = UserRole.ADMIN
            else:
                user_role = UserRole.USER

            logger.debug("Роль пользователя с `username`='%s': %s была передана в контекст", username, user_role)

            await state.update_data(user_role=user_role)

            data["start_registration"] = True
        else:
            data["start_registration"] = None

        await state.update_data(user_row=user_row)

        result = await handler(event, data)

        logger.debug("Выходим из RegistrationMiddleware")

        return result

