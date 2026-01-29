import logging

from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_source_by_id, get_term_by_id, get_term_by_name
from database.models import Source, Term
from exceptions import (
    TermNotFoundByIdError,
    TermNotFoundByNameError,
    TermPresentationError,
)
from services.terms import get_term_info

logger = logging.getLogger(__name__)


class TermService:
    async def get_term(self, session: AsyncSession, *, term_name: str, i18n: dict):
        term: Term = await get_term_by_name(session, name=term_name)
        if term is None:
            logger.debug("Не удалось найти термин `name=%s` в базе данных", term_name)
            raise TermNotFoundByNameError(term_name)

        text, kb = await get_term_info(term=term, i18n=i18n)
        if text is None:
            logger.debug(
                "Не удалось получить информацию о термине `name=%s` с помощью сервиса",
                term_name,
            )
            raise TermPresentationError(term_name)

        return text, kb

    async def get_definition(
        self,
        session: AsyncSession,
        *,
        term_id: int,
        source_id: int,
        index: int = 0,
        i18n: dict,
    ):
        term: Term = await get_term_by_id(session, id=term_id)
        source: Source = await get_source_by_id(session, id=source_id)

        if term is None:
            logger.debug("Не удалось найти термин `id=%s` в базе данных", term_id)
            raise TermNotFoundByIdError(term_id)

        text, kb = await get_term_info(term=term, source=source, index=index, i18n=i18n)
        if text is None:
            logger.debug(
                "Не удалось перейти к источнику/дефиниции у термина с `name`='%s'",
                term.name,
            )
            raise TermPresentationError()

        return text, kb
