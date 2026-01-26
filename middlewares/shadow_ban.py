import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User

from database.models import Users

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

        username: str = user.username if user.username else user.first_name

        db_user: Users = data.get("db_user")

        if db_user is None:
            logger.debug("Данные о пользователе с с `username`='%s' не удалось получить из базы данных", username)
            return await handler(event, data)

        user_banned_status: bool = db_user.banned

        if user_banned_status:
            logger.warning(
                "Забаненный пользователь с `username`='%s', `user_id`='%d' попытался взаимодействовать с ботом, игнорируем апдейт",
                username, user.id)
            if event.callback_query:
                await event.callback_query.answer()
            return

        logger.warning("Пользователь с `username`='%s' не в бане, переходим в следующий \"обработчик\"", username)

        result = await handler(event, data)

        logger.debug("Выходим из ShadowBanMiddleware")

        return result