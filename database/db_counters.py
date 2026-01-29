import logging

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models import Term, Users

logger = logging.getLogger(__name__)


async def get_total_users(sessionmaker: async_sessionmaker[AsyncSession]) -> int | None:
    async with sessionmaker() as session:
        try:
            async with session.begin():
                result = await session.execute(select(func.count(Users.id)))

                total_users_count: int = result.scalar_one_or_none()

                return total_users_count
        except Exception as e:
            logger.exception("Транзакция откатилась из-за ошибки: %s", e)
            raise


async def get_total_terms(sessionmaker: async_sessionmaker[AsyncSession]) -> int | None:
    async with sessionmaker() as session:
        try:
            async with session.begin():
                result = await session.execute(select(func.count(Term.id)))

                total_terms_count: int = result.scalar_one_or_none()

                return total_terms_count
        except Exception as e:
            logger.exception("Транзакция откатилась из-за ошибки: %s", e)
            raise
