import logging

from database.db import get_users_feature_usage_count
from enums.features import Feature

logger = logging.getLogger(__name__)


async def is_user_allowed_to_use_feature(
    session,
    *,
    user_id: int,
    feature: Feature,
) -> tuple[bool, int | None]:
    usage_count = await get_users_feature_usage_count(
        session,
        user_id=user_id,
        feature=feature,
    )

    usage_limit = feature.limit

    if usage_count is None:
        logger.debug(
            "Не удалось получить количество использований фичи `feature_name`='%s' для пользователя с `user_id`='%d'",
            feature.name,
            user_id,
        )
        return True, None  # Разрешаем использование по умолчанию

    if usage_count >= usage_limit:
        logger.warning(
            "Пользователь с `user_id`='%d' превысил лимит использования фичи `feature_name`='%s'",
            user_id,
            feature.name,
        )
        return False, None  # Пользователь превысил лимит использования фичи

    logger.debug(
        "Пользователь с `user_id`='%d' может использовать фичу `feature_name`='%s' (использовано %d раз)",
        user_id,
        feature.name,
        usage_count,
    )
    return True, usage_count  # Пользователь может использовать фичу
