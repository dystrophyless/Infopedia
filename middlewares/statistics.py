import logging
from typing import Any, Awaitable, Callable

from aiogram.fsm.context import FSMContext
from psycopg import AsyncConnection

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User

from database.db import add_user_activity

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

        result = await handler(event, data)

        state: FSMContext = data.get("state")

        user_row = await state.get_value("user_row")

        logger.debug("Строка о пользователе: %s", user_row)

        if user_row is None:
            logger.debug("Данные о пользователе не удалось получить из базы данных, переходим в следующий \"обработчик\"")
            return result

        logger.debug("Добавляем активность пользователя в БД")

        conn: AsyncConnection = data.get("conn")

        if conn is None:
            logger.error("Соединение с базой данных не было найдено в данных мидлвари")
            raise RuntimeError("Отстуствует соединение с базой данных для проверки теневого бана")

        await add_user_activity(conn, user_id=user.id)

        logger.debug("Выходим из ShadowBanMiddleware")

        return result