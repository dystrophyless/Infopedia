import logging
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import FeatureUsage
from enums.features import Feature

logger = logging.getLogger(__name__)


async def log_feature_usage(
    session: AsyncSession,
    *,
    user_id: int,
    feature: Feature,
) -> None:
    new_usage = FeatureUsage(user_id=user_id, feature_name=feature.name)
    session.add(new_usage)

    logger.debug(
        "Использование функции с `feature_name`='%s' было зафиксировано для пользователя с `user_id`='%d'",
        feature.name,
        user_id,
    )


async def get_users_feature_usage_count(
    session: AsyncSession,
    *,
    user_id: int,
    feature: Feature,
) -> int | None:
    threshold = datetime.now() - timedelta(days=30)

    result = await session.execute(
        select(func.count(FeatureUsage.id)).where(
            FeatureUsage.user_id == user_id,
            FeatureUsage.feature_name == feature.name,
            FeatureUsage.created_at >= threshold,
        ),
    )

    usage_count: int = result.scalar_one_or_none()

    if usage_count is None:
        logger.debug(
            "Не удалось получить количество использований функции с `feature_name`='%s' для пользователя с `user_id`='%d'",
            feature.name,
            user_id,
        )
        return None

    return usage_count
