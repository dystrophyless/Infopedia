import logging
from typing import Any, Awaitable, Callable


from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User

from sqlalchemy.ext.asyncio import AsyncSession

from database.db import add_user_activity
from database.models import Users

logger = logging.getLogger(__name__)


class ActivityCounterMiddleware(BaseMiddleware):
    async def __call__(self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any]
    ) -> Any:
        logger.debug("Входим в ActivityCounterMiddleware")

        user: User = data.get("event_from_user")

        if user is None:
            logger.warning("По какой-то неизвестной причине пользователя не удалось определить, переходим в следующий \"обработчик\"")
            return await handler(event, data)

        username = user.username if user.username else user.first_name

        result = await handler(event, data)

        db_user: Users = data.get("db_user")

        if db_user is None:
            logger.debug("Данные о пользователе с `username`='%s' не удалось получить из базы данных, переходим в следующий \"обработчик\"", username)
            return result

        logger.debug("Добавляем активность пользователя с `username`='%s' в БД", username)

        session: AsyncSession = data.get("session")

        if session is None:
            logger.error("Соединение с базой данных не было найдено в данных мидлвари")
            raise RuntimeError("Отсутствует соединение с базой данных для того что бы считать активность")

        await add_user_activity(session, user_id=user.id)

        logger.debug("Выходим из ShadowBanMiddleware")

        return result