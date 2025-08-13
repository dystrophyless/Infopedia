import logging

from aiogram import Router
from aiogram.types import InlineQuery, InlineQueryResultArticle

from services.search import search_definitions

logger = logging.getLogger(__name__)

router = Router()

@router.inline_query()
async def process_search_mode(inline_query: InlineQuery, indexed_terms: list[dict[str, str]]) -> None:
    query: str = inline_query.query.lower()
    user_id: int = inline_query.from_user.id
    results: list[InlineQueryResultArticle] = search_definitions(query, user_id, indexed_terms)

    await inline_query.answer(results, cache_time=1)
