import logging

from sqlalchemy.ext.asyncio import AsyncSession

from database.models import UserFeedback


logger = logging.getLogger(__name__)


async def add_search_feedback(
    session: AsyncSession,
    *,
    user_id: int,
    definition_id: int,
    query: str,
    correct: bool
) -> None:
    new_feedback: UserFeedback = UserFeedback(
        user_id=user_id,
        definition_id=definition_id,
        query=query,
        correct=correct
    )

    session.add(new_feedback)

    logger.debug(
        "Фидбэк по поиску по определению был добавлен в базу данных. "
        "user_id='%d', `definition_id`='%d', `query`='%s', `correct`='%s'",
        user_id,
        definition_id,
        query,
        correct,
    )