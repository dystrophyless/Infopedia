import logging

from rapidfuzz import fuzz
import random
import uuid

from aiogram.types import InlineQueryResultArticle, InputTextMessageContent

from services.signature import generate_payload
from services.text import normalize

logger = logging.getLogger(__name__)


def _get_random_terms(count: int, user_id: int, indexed_terms: list[dict[str, str]]) -> list[InlineQueryResultArticle]:
    sampled = random.sample(indexed_terms, k=min(count, len(indexed_terms)))
    results = []

    for term_entry in sampled:
        term = term_entry["term"]
        sources = term_entry["sources"]

        first_source = next(iter(sources.values()))
        first_definition = first_source[0]["definition"]

        message = generate_payload({
            "action": "get_term_info",
            "user_id": user_id,
            "term": term
        })

        results.append(
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title=term,
                description=first_definition[:250],
                input_message_content=InputTextMessageContent(
                    message_text=message
                )
            )
        )

    return results


def search_definitions(query: str, user_id: int, indexed_terms: list[dict[str, str]]) -> list[InlineQueryResultArticle]:
    normalized_query: str = normalize(query)
    results = []

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
        results.extend(_get_random_terms(10, user_id, indexed_terms))
    else:
        matched = []

        for term_entry in indexed_terms:
            if normalized_query == term_entry["normalized"]:
                matched.append((100, term_entry))

        for term_entry in indexed_terms:
            if term_entry["normalized"].startswith(normalized_query):
                matched.append((90, term_entry))

        if len(normalized_query) >= 3:
            for term_entry in indexed_terms:
                score = fuzz.partial_ratio(normalized_query, term_entry["normalized"])
                if score >= 85:
                    matched.append((score, term_entry))

        unique_matched = sorted(matched, key=lambda x: x[0], reverse=True)
        seen_terms = set()
        top_results = []

        for score, term_entry in unique_matched:
            term = term_entry["term"]
            if term in seen_terms:
                continue
            seen_terms.add(term)

            sources = term_entry["sources"]
            first_source = next(iter(sources.values()))
            first_definition = first_source[0]["definition"]

            message = generate_payload({
                "action": "get_term_info",
                "user_id": user_id,
                "term": term
            })

            result = InlineQueryResultArticle(
                id=f"result_{uuid.uuid4().hex[:8]}",
                title=term,
                description=first_definition[:250],
                input_message_content=InputTextMessageContent(
                    message_text=message
                )
            )
            top_results.append(result)

            if len(top_results) >= 10:
                break

        results.extend(top_results)

        if not results:
            message_not_found = generate_payload({
                "action": "definition_was_not_found",
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
