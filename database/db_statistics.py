import logging

from sqlalchemy import func, select, case, Float, Integer
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Users, Activity, Term, Source, Definition, UserFeedback
from schemas.user import UserStat
from schemas.feedback import FeedbackStat


logger = logging.getLogger(__name__)


async def get_activity_statistics_individually(
    session: AsyncSession,
) -> list[UserStat] | None:
    query = (
        select(
            Activity.user_id,
            func.sum(Activity.actions),
            Users.username,
            Users.first_name,
        )
        .join(Users, Users.user_id == Activity.user_id)
        .group_by(Activity.user_id, Users.username, Users.first_name)
        .order_by(func.sum(Activity.actions).desc())
        .limit(5)
    )

    result = await session.execute(query)

    rows = result.all()

    if not rows:
        logger.debug(
            "Не удалось получить статистику активности пользователей из базы данных"
        )
        return None

    statistics: list[UserStat] = [
        UserStat(
            user_id=user_id,
            username=username,
            first_name=first_name,
            total_actions=total_actions,
        )
        for user_id, total_actions, username, first_name in rows
    ]

    logger.debug(
        "Была получена статистика активности пользователей с таблицы `activity`"
    )
    return statistics


async def get_activity_statistics_generally(session: AsyncSession) -> int | None:
    query = select(func.sum(Activity.actions))

    result = await session.execute(query)

    total_actions: int = result.scalar_one_or_none()

    if total_actions is None:
        logger.debug(
            "Не удалось получить общее количество действий выполненными всеми пользователями за сегодня"
        )
        return None

    return total_actions


async def get_search_statistics_individually(
    session: AsyncSession, limit: int = 10
) -> list[FeedbackStat] | None:
    query = (
        select(
            Definition.id,
            Term.name,
            func.count(UserFeedback.id),
            func.sum(case((UserFeedback.correct == True, 1), else_=0)),
            (
                (
                    func.sum(case((UserFeedback.correct == True, 1), else_=0)).cast(
                        Float
                    )
                    / func.count(UserFeedback.id).cast(Float)
                    * 100
                ).cast(Integer)
            ).label("accuracy"),
        )
        .join(UserFeedback, UserFeedback.definition_id == Definition.id)
        .join(Source, Source.id == Definition.source_id)
        .join(Term, Term.id == Source.term_id)
        .group_by(Definition.id, Term.name)
        .having(
            (
                func.sum(case((UserFeedback.correct == True, 1), else_=0))
                / func.count(UserFeedback.id)
                * 100
            )
            <= 70
        )
        .order_by("accuracy")
        .limit(limit)
    )

    result = await session.execute(query)
    rows = result.all()

    if not rows:
        logger.debug(
            "Не удалось получить индивидуальную статистику точности поиска по определению из базы данных"
        )
        return None

    statistics: list[FeedbackStat] = [
        FeedbackStat(
            definition_id=definition_id,
            term_name=term_name,
            total_queries=total_queries,
            correct_queries=correct_queries,
            accuracy=accuracy,
        )
        for definition_id, term_name, total_queries, correct_queries, accuracy in rows
    ]

    logger.debug(
        "Была получена индивидуальная статистика точности поиска по определению из базы данных"
    )
    return statistics


async def get_search_statistics_generally(
    session: AsyncSession,
) -> tuple[int, int] | None:
    query = select(
        func.count(UserFeedback.id),
        (
            (
                func.sum(case((UserFeedback.correct == True, 1), else_=0)).cast(Float)
                / func.count(UserFeedback.id).cast(Float)
                * 100
            ).cast(Integer)
        ).label("accuracy"),
    )

    result = await session.execute(query)
    rows = result.one_or_none()

    if not rows:
        logger.debug(
            "Не удалось получить общую статистику точности поиска по определению из базы данных"
        )
        return None

    total_queries, accuracy = rows

    return total_queries, accuracy
