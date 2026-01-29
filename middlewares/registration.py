import logging
from typing import Any, Awaitable, Callable
from sqlalchemy.ext.asyncio import AsyncSession

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User
from aiogram.fsm.context import FSMContext

from enums.roles import UserRole
from database.db import get_user
from database.models import Users

logger = logging.getLogger(__name__)


class RegistrationMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        logger.debug("Входим в RegistrationMiddleware")

        user: User = data.get("event_from_user")

        if user is None:
            logger.warning(
                'По какой-то неизвестной причине пользователя не удалось определить, переходим в следующий "обработчик"'
            )
            return await handler(event, data)

        session: AsyncSession = data.get("session")

        if session is None:
            logger.error("Соединение с базой данных не было найдено в данных мидлвари")
            raise RuntimeError(
                "Отсутствует соединение с базой данных для проверки зарегистрирован ли пользователь"
            )

        username: str = user.username if user.username else user.first_name

        db_user: Users = await get_user(session, user_id=user.id)

        state: FSMContext = data.get("state")

        if db_user is None:
            logger.debug(
                "Данные о пользователе с `username`='%s' не удалось получить из базы данных, определяем роль пользователя, передаём в контекст, устанавливаем состояние регистрации, переходим в следующий \"обработчик\"",
                username,
            )

            admin_ids: list[int] = data.get("admin_ids")
            if user.id in admin_ids:
                user_role = UserRole.ADMIN
            else:
                user_role = UserRole.USER

            logger.debug(
                "Роль пользователя с `username`='%s': %s была передана в контекст",
                username,
                user_role,
            )

            await state.update_data(user_role=user_role)

            data["start_registration"] = True
        else:
            logger.debug(
                "Строка о пользователе с `username`='%s':"
                "user_id='%d', `language`='%s', `grade`='%s', `role`='%s', `is_alive`='%s', `banned`='%s'",
                username,
                db_user.user_id,
                db_user.language,
                db_user.grade,
                db_user.role,
                db_user.is_alive,
                db_user.banned,
            )

            data["start_registration"] = None

        data["db_user"] = db_user

        result = await handler(event, data)

        logger.debug("Выходим из RegistrationMiddleware")

        return result
