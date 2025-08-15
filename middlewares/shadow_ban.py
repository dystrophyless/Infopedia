import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User
from aiogram.fsm.context import FSMContext


logger = logging.getLogger(__name__)


class ShadowBanMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any]
    ) -> Any:
        logger.debug("Входим в ShadowBanMiddleware")

        user: User = data.get("event_from_user")

        if user is None:
            logger.warning("По какой-то неизвестной причине пользователя не удалось определить, переходим в следующий \"обработчик\"")
            return await handler(event, data)

        state: FSMContext = data.get("state")

        user_row = await state.get_value("user_row")

        if user_row is None:
            logger.debug("Данные о пользователе не удалось получить из базы данных")
            return await handler(event, data)

        user_banned_status = user_row[7]

        if user_banned_status:
            logger.warning("Забаненный пользователь с `user_id`='%d' попытался взаимодействовать с ботом, игнорируем апдейт", user.id)
            if event.callback_query:
                await event.callback_query.answer()
            return

        logger.warning("Пользователь не в бане, переходим в следующий \"обработчик\"")

        result = await handler(event, data)

        logger.debug("Выходим из ShadowBanMiddleware")

        return result