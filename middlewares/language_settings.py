import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import TelegramObject, User


logger = logging.getLogger(__name__)


class LanguageSettingsMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        logger.debug("Входим в LanguageSettingsMiddleware")

        user: User = data.get("event_from_user")

        if user is None:
            logger.warning(
                'По какой-то неизвестной причине пользователя не удалось определить, переходим в следующий "обработчик"'
            )
            return await handler(event, data)

        if event.callback_query is None:
            logger.warning(
                'Данный апдейт не является типа callback_query, переходим в следующий "обработчик"'
            )
            return await handler(event, data)

        username: str = user.username if user.username else user.first_name

        locales: list[str] = data.get("locales")

        state: FSMContext = data.get("state")

        if event.callback_query.data == "cancel_language_button_data":
            logger.debug(
                "Так как пользователь с `username`='%s' нажал отменить при выборе языка, устанавливаем `user_language`='None'",
                username,
            )
            await state.update_data(user_language=None)
        elif (
            event.callback_query.data in locales
            and event.callback_query.data != await state.get_value("user_language")
        ):
            logger.debug(
                "Так как пользователь с `username`='%s' нажал на одну из кнопок с языком и нынешний язык пользователя не равен тому, что пользователь выбрал, устанавливаем `user_language`='%s' в данных состояний",
                username,
                event.callback_query.data,
            )
            await state.update_data(user_language=event.callback_query.data)

        result = await handler(event, data)

        logger.debug("Выходим из LanguageSettingsMiddleware")

        return result
