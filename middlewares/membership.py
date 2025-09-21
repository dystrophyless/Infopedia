import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User
from aiogram.fsm.context import FSMContext

from services.membership import is_user_followed
from database.models import Users

logger = logging.getLogger(__name__)


class MembershipMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        logger.debug("Входим в MembershipMiddleware")

        user: User = data.get("event_from_user")

        if user is None:
            logger.warning("По какой-то неизвестной причине пользователя не удалось определить, переходим в следующий \"обработчик\"")
            return await handler(event, data)


        username: str = user.username if user.username else user.first_name

        bot = data.get("bot")
        channel_id = data.get("channel_id")
        state: FSMContext = data.get("state")

        db_user: Users = data.get("db_user")



        if db_user is None:
            logger.debug("Данные о пользователе с `username`='%s' не удалось получить из базы данных, переходим в следующий \"обработчик\"", username)
            return await handler(event, data)

        is_following = await is_user_followed(bot, user.id, channel_id)

        await_membership = await state.get_value("await_membership")

        if not is_following:
            logger.debug(
                "Пользователь с `username`='%s' был не подписан, устанавливаем состояние ожидания подписки, переходим в следующий \"обработчик\"",
                username)
            if await_membership:
                data["await_membership"] = True
            else:
                data["await_membership"] = None
        else:
            logger.debug("Пользователь с `username`='%s' был подписан, переходим в следующий \"обработчик\"", username)


        result = await handler(event, data)

        logger.debug("Выходим из MembershipMiddleware")

        return result