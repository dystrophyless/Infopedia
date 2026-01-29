import logging
from html import escape

from database.models import Term, Source, Definition
from keyboards.inline_keyboards import build_sources_kb
from exceptions import NoSourcesFoundError


logger = logging.getLogger(__name__)


async def get_term_info(
    *, term: Term, source: Source = None, index: int = 0, i18n: dict
):
    if source is None:
        sources: list[Source] = term.sources

        source: Source = sources[0]

    definition, topic, page = await _get_term_details(source=source, index=index)

    text = i18n.get("get_term_info").format(
        term=term.name, text=definition, topic=topic, page=page
    )
    kb = build_sources_kb(term=term, current_source=source, current_index=index)

    return text, kb


async def _get_term_details(
    *,
    source: Source,
    index: int = 0,
) -> tuple[str, str, int] | None:
    definitions: list[Definition] = source.definitions
    term_name: str = source.term.name

    if not definitions:
        logging.debug(
            f"У источника {source} не найдены дефиниции для термина {term_name}."
        )
        raise NoSourcesFoundError

    indexed_definition: Definition = definitions[index]

    definition: str = escape(indexed_definition.text)
    topic: str = escape(indexed_definition.topic)
    page: int = indexed_definition.page

    return definition, topic, page
