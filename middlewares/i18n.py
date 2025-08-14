import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import TelegramObject, User


logger = logging.getLogger(__name__)


class TranslatorMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        logger.debug("Входим в TranslatorMiddleware")

        user: User = data.get("event_from_user")

        if user is None:
            logger.warning("По какой-то неизвестной причине пользователя не удалось определить, переходим в следующий \"обработчик\"")
            return await handler(event, data)

        state: FSMContext = data.get("state")

        if (user_language := await state.get_value("user_language")) is None:
            user_row = await state.get_value("user_row")

            if user_row is not None:
                user_language = user_row[3]
                logger.debug("Получили из базы данных следующий язык: %s", user_language)
            else:
                logger.debug("Данные о пользователе не удалось получить из базы данных")

            if user_language is None:
                logger.debug("Так-как язык не был найден ни в контексте, ни в базе данных, устанавливаем системный язык пользователя: %s", user.language_code)
                user_language = user.language_code

        translations: dict = data.get("translations")
        i18n: dict = translations.get(user_language)

        if i18n is None:
            logger.debug("Для языка пользователя не нашлось словаря, поэтому устанавливаем дефолтный язык: %s", translations["default"])
            data["i18n"] = translations[translations["default"]]
        else:
            logger.debug("Устанавливаем следующий словарь языка: %s", user_language)
            data["i18n"] = i18n

        result = await handler(event, data)

        logger.debug("Выходим из TranslatorMiddleware")

        return result