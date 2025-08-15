import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User
from aiogram.fsm.context import FSMContext

from fsm.states import FSMMembership
from services.membership import is_user_followed

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

        bot = data.get("bot")
        channel_id = data.get("channel_id")
        state: FSMContext = data.get("state")

        user_row = await state.get_value("user_row")

        logger.debug("Строка о пользователе: %s", user_row)

        if user_row is None:
            logger.debug("Данные о пользователе не удалось получить из базы данных, переходим в следующий \"обработчик\"")
            return await handler(event, data)

        is_following = await is_user_followed(bot, user.id, channel_id)

        if not is_following:
            logger.debug("Пользователь был не подписан, устанавливаем состояние ожидания подписки, переходим в следующий \"обработчик\"")
            await state.set_state(FSMMembership.await_membership)

        result = await handler(event, data)

        logger.debug("Выходим из MembershipMiddleware")

        return result