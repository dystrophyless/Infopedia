import logging

from aiogram import Router
from aiogram.types import InlineQuery, InlineQueryResultArticle

from sqlalchemy.ext.asyncio import AsyncSession

from services.search import search_definitions

logger = logging.getLogger(__name__)

router = Router()

@router.inline_query()
async def process_search_mode(inline_query: InlineQuery, session: AsyncSession) -> None:
    query: str = inline_query.query.lower()
    user_id: int = inline_query.from_user.id
    results: list[InlineQueryResultArticle] = await search_definitions(session, query=query, user_id=user_id)

    await inline_query.answer(results, cache_time=1)
