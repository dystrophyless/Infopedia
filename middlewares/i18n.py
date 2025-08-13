import logging
from typing import Any, Awaitable, Callable
from psycopg import AsyncConnection

from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import TelegramObject, User

from database.db import get_user_language


logger = logging.getLogger(__name__)


class TranslatorMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
                       ) -> Any:
        user: User = data.get("event_from_user")

        if user is None:
            return await handler(event, data)

        state: FSMContext = data.get("state")
        user_context_data = await state.get_data()

        if (user_language := user_context_data.get("user_language")) is None:
            conn: AsyncConnection = data.get("conn")

            if conn is None:
                logger.error("Подключение к базе данных не было найдено в миддлварях")
                raise RuntimeError("Отсутствует подключение к базе данных для определения языка пользователя")

            user_language: str | None = await get_user_language(conn, user_id=user.id)
            if user_language is None:
                user_language = user.language_code

        translations: dict = data.get("translations")
        i18n: dict = translations.get(user_language)

        if i18n is None:
            data["i18n"] = translations[translations["default"]]
        else:
            data["i18n"] = i18n

        return await handler(event, data)