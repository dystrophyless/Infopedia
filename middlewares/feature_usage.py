import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.dispatcher.flags import get_flag
from aiogram.types import TelegramObject

from database.db import log_feature_usage

logger = logging.getLogger(__name__)


class FeatureUsageMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        logger.debug("Входим в MenuHistoryMiddleware")

        log_feature_flag = get_flag(data, "log_feature")

        log_feature = log_feature_flag.get("feature") if log_feature_flag else None

        result = await handler(event, data)

        if log_feature:
            session = data.get("session")
            user_id = event.from_user.id

            await log_feature_usage(session, user_id=user_id, feature=log_feature)

        logger.debug("Выходим из MenuHistoryMiddleware")

        return result
