import logging

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Term, Source, Definition

from abc import ABC, abstractmethod


logger = logging.getLogger(__name__)


class SearchStrategy(ABC):
    @abstractmethod
    async def search(
        self, session: AsyncSession, *, query: str, limit: int
    ) -> list[Term] | None:
        pass


class PrefixSearchStrategy(SearchStrategy):
    def __init__(self, *, is_prefix: bool = True):
        self.is_prefix = is_prefix

    async def search(
        self, session: AsyncSession, *, query: str, limit: int
    ) -> list[Term] | None:
        like_pattern: str = f"{query}%" if self.is_prefix else f"%{query}%"

        result = await session.execute(
            select(Term).where(Term.name.ilike(like_pattern)).limit(limit)
        )

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
        self, session: AsyncSession, *, query: str, limit: int
    ) -> list[Term] | None:
        result = await session.execute(
            select(Term)
            .where(Term.name.op("%")(query))
            .order_by(func.similarity(Term.name, query).desc())
            .limit(limit)
        )

        terms = list(result.scalars().all())

        if not terms:
            logger.debug("Не удалось получить термины похожие на `%s`", query)
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
        self, session: AsyncSession, *, query: str, limit: int = 10
    ) -> list[Term] | None:
        return await self._strategy.search(session, query=query, limit=limit)


async def get_definition_candidates(session, qvec_list, top_k: int):
    stmt = (
        select(
            Definition,
            (1 - Definition.embedding.cosine_distance(qvec_list)).label("sim_approx"),
        )
        .options(selectinload(Definition.source).selectinload(Source.term))
        .order_by(Definition.embedding.cosine_distance(qvec_list))
        .limit(top_k)
    )
    result = await session.execute(stmt)
    return result.all()
