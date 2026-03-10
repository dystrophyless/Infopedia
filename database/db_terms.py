import logging

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Source, Term, Definition

logger = logging.getLogger(__name__)


async def get_term_by_name(session: AsyncSession, *, name: str) -> Term | None:
    query = (
        select(Term)
        .where(Term.name == name)
        .options(
            selectinload(Term.sources)
            .selectinload(Source.definitions)
            .joinedload(Definition.topic)
        )
    )
    result = await session.execute(query)

    if result is None:
        logger.debug("Не удалось получить термин с `name`='%s' из базы данных", name)
        return None

    term: Term = result.scalar_one_or_none()

    return term


async def get_term_by_id(session: AsyncSession, *, id: int) -> Term | None:
    query = (
        select(Term)
        .where(Term.id == id)
        .options(
            selectinload(Term.sources),
        )
    )
    result = await session.execute(query)

    if result is None:
        logger.debug("Не удалось получить термин с `id`='%s' из базы данных", id)
        return None

    term: Term = result.scalar_one_or_none()

    return term


async def get_source_by_id(session: AsyncSession, *, id: int) -> Source | None:
    query = (
        select(Source)
        .where(Source.id == id)
        .options(
            selectinload(Source.definitions)
            .joinedload(Definition.topic)
        )
    )
    result = await session.execute(query)

    if result is None:
        logger.debug("Не удалось получить источник с `id`='%s' из базы данных", id)
        return None

    source: Source = result.scalar_one_or_none()

    return source


async def get_random_terms(
    session: AsyncSession,
    *,
    quantity: int,
) -> list[Term] | None:
    query = (
        select(Term)
        .order_by(func.random())
        .limit(quantity)
        .options(
            selectinload(Term.sources)
            .selectinload(Source.definitions)
            .joinedload(Definition.topic)
        )
    )
    result = await session.execute(query)

    if result is None:
        logger.debug("Не удалось получить рандомные термины из базы данных")
        return None

    terms: list[Term] = list(result.scalars().all())

    return terms


async def search_terms_by_prefix(
    session: AsyncSession,
    *,
    query: str,
    limit: int = 10,
    prefix: bool = True,
) -> list[Term] | None:
    like: str = f"{query}%" if prefix else f"%{query}%"
    result = await session.execute(
        select(Term).where(Term.name.ilike(like)).limit(limit),
    )

    if result is None:
        logger.debug(
            "Не удалось получить термины которые начинаются на `query=%s` из базы данных",
            query,
        )
        return None

    terms: list[Term] = list(result.scalars().all())

    return terms


async def search_terms_by_similarity(
    session: AsyncSession,
    *,
    query: str,
    limit: int = 10,
) -> list[Term] | None:
    result = await session.execute(
        select(Term)
        .where(Term.name.op("%")(query))
        .order_by(func.similarity(Term.name, query).desc())
        .limit(limit),
    )

    if result is None:
        logger.debug(
            "Не удалось получить термины похожие на `query=%s` из базы данных",
            query,
        )
        return None

    terms: list[Term] = list(result.scalars().all())

    return terms
