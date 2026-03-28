import logging
from abc import ABC, abstractmethod

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from database.models import Topic, Term, Definition

logger = logging.getLogger(__name__)


class SearchStrategy(ABC):
    @abstractmethod
    async def search(
        self,
        session: AsyncSession,
        *,
        query: str,
        limit: int,
    ) -> list[Term] | None:
        pass


class PrefixSearchStrategy(SearchStrategy):
    def __init__(self, *, is_prefix: bool = True):
        self.is_prefix = is_prefix

    async def search(
        self,
        session: AsyncSession,
        *,
        query: str,
        limit: int,
    ) -> list[Term] | None:
        like_pattern: str = f"{query}%" if self.is_prefix else f"%{query}%"

        query = (
            select(Term)
            .where(Term.name.ilike(like_pattern))
            .limit(limit)
            .options(
                selectinload(Term.definitions)
            )
        )
        result = await session.execute(query)

        terms = list(result.scalars().all())

        if not terms:
            logger.debug(
                "Не удалось получить термины по паттерну `%s` (prefix=%s)",
                query,
                self.is_prefix,
            )
            return None

        return terms


class SimilaritySearchStrategy(SearchStrategy):
    async def search(
        self,
        session: AsyncSession,
        *,
        user_query: str,
        limit: int,
    ) -> list[Term] | None:
        query = (
            select(Term)
            .where(Term.name.op("%")(user_query))
            .order_by(func.similarity(Term.name, user_query).desc())
            .limit(limit)
            .options(
                selectinload(Term.definitions)
            )
        )
        result = await session.execute(query)

        terms = list(result.scalars().all())

        if not terms:
            logger.debug("Не удалось получить термины похожие на `%s`",  user_query)
            return None

        return terms


class SearchContext:
    def __init__(self, strategy: SearchStrategy) -> None:
        self._strategy = strategy

    @property
    def strategy(self) -> SearchStrategy:
        return self._strategy

    @strategy.setter
    def strategy(self, strategy: SearchStrategy) -> None:
        self._strategy = strategy

    async def execute_search(
        self,
        session: AsyncSession,
        *,
        query: str,
        limit: int = 10,
    ) -> list[Term] | None:
        return await self._strategy.search(session, query=query, limit=limit)


async def get_definition_candidates(session, qvec_list, top_k: int):
    query = (
        select(
            Definition,
            (1 - Definition.embedding.cosine_distance(qvec_list)).label("sim_approx"),
        )
        .order_by(Definition.embedding.cosine_distance(qvec_list))
        .limit(top_k)
        .options(
            joinedload(Definition.term),
            joinedload(Definition.topic)
            .joinedload(Topic.book)
        )
    )
    result = await session.execute(query)
    return result.all()
