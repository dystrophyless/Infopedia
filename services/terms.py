import logging
from html import escape

from database.models import Term, Source, Definition
from keyboards.inline_keyboards import build_sources_kb


logger = logging.getLogger(__name__)

async def get_term_info(
    *,
    term: Term,
    source: Source = None,
    index: int = 0,
    i18n: dict
):
    if source is None:
        sources: list[Source] = term.sources

        source: Source = sources[0]

        source_definition: Definition = source.definitions[0]

        definition: str = escape(source_definition.text)
        topic: str = escape(source_definition.topic)
        page: int = source_definition.page
    else:
        definitions: list[Definition] = source.definitions

        if not definitions:
            logging.debug(f"У источника {source} не найдены дефиниции для термина {term}.")
            return

        indexed_definition: Definition = definitions[index]

        definition: str = escape(indexed_definition.text)
        topic: str = escape(indexed_definition.topic)
        page: int = indexed_definition.page

    text = i18n.get("get_term_info").format(term.name, definition, topic, page)
    kb = build_sources_kb(term=term, current_source=source, current_index=index)

    return text, kb