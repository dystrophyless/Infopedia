import logging

import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent

from database.models import Term, Source, Definition
from database.db import get_random_terms, search_terms_by_prefix, search_terms_by_similarity

from services.signature import generate_payload

logger = logging.getLogger(__name__)


async def _get_ready_random_terms(
    session: AsyncSession,
    *,
    quantity: int,
    user_id: int
) -> list[InlineQueryResultArticle]:
    results: list[InlineQueryResultArticle] = []

    random_terms: list[Term] = await get_random_terms(session, quantity=quantity)

    for term in random_terms:
        sources: list[Source] = term.sources

        first_source: Source = sources[0]
        first_definition: Definition = first_source.definitions[0]

        message = generate_payload({
            "action": "get_term_info",
            "user_id": user_id,
            "term": term.name
        })

        results.append(
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title=term.name,
                description=first_definition.text[:250],
                input_message_content=InputTextMessageContent(
                    message_text=message
                )
            )
        )

    return results


async def search_definitions(
    session: AsyncSession,
    *,
    query: str,
    user_id: int
) -> list[InlineQueryResultArticle]:
    results: list[InlineQueryResultArticle] = []

    if not query.strip():
        message = generate_payload({
            "action": "go_back_to_search",
            "user_id": user_id,
        })

        results.append(
            InlineQueryResultArticle(
                id=f'RandomTermins_{uuid.uuid4().hex[:8]}',
                title='Ниже список рандомных терминов',
                description='Введите нужный термин, и список обновится.',
                input_message_content=InputTextMessageContent(
                    message_text=message
                )
            )
        )
        results.extend(await _get_ready_random_terms(session, quantity=10, user_id=user_id))
    else:
        if len(query) < 3:
            found_terms: list[Term] = await search_terms_by_prefix(session, query=query)
        else:
            prefix_terms: list[Term] = await search_terms_by_prefix(session, query=query, prefix=False) or []
            sim_terms: list[Term] = await search_terms_by_similarity(session, query=query) or []

            unique_terms: dict[int, Term] = {t.id: t for t in prefix_terms + sim_terms}
            found_terms: list[Term] = list(unique_terms.values())

        for term in found_terms:
            sources: list[Source] = term.sources

            first_source: Source = sources[0]
            first_definition: Definition = first_source.definitions[0]

            message = generate_payload({
                "action": "get_term_info",
                "user_id": user_id,
                "term": term.name
            })

            result = InlineQueryResultArticle(
                id=f"result_{uuid.uuid4().hex[:8]}",
                title=term.name,
                description=first_definition.text[:250],
                input_message_content=InputTextMessageContent(
                    message_text=message
                )
            )

            results.append(result)

        if not results:
            message_not_found = generate_payload({
                "action": "term_was_not_found",
                "user_id": user_id
            })
            message_suggest_new_term = generate_payload({
                "action": "suggest_new_term",
                "user_id": user_id,
                "term": query
            })
            results.append(
                InlineQueryResultArticle(
                    id=f'NotFound_{uuid.uuid4().hex[:8]}',
                    title='Такого термина в боте не найдено',
                    description='Проверьте правильность ввода и попробуйте ещё раз.',
                    input_message_content=InputTextMessageContent(
                        message_text=message_not_found
                    )
                )
            )
            results.append(
                InlineQueryResultArticle(
                    id=f'SuggestNewTermin_{uuid.uuid4().hex[:8]}',
                    title='Предложить данный термин',
                    description='Если введёный вами термин есть в книге, но его нет в боте - вы можете предложить добавить его.',
                    input_message_content=InputTextMessageContent(
                        message_text=message_suggest_new_term
                    )
                )
            )

    return results
