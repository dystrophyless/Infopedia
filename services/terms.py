import logging
from html import escape

from database.models import Book, Term, Definition
from keyboards.inline_keyboards import build_books_kb

logger = logging.getLogger(__name__)


async def get_term_info(
    *,
    term: Term,
    book: Book = None,
    index: int = 0,
    i18n: dict,
):
    books: list[Book] = get_term_books(term=term)

    if book is None:
        book: Book = books[0]

    definitions: list[Definition] = get_term_definitions_in_specific_book(term=term, book=book)

    indexed_definition: Definition = definitions[index]

    definition: str = escape(indexed_definition.text)
    topic: str = escape(indexed_definition.topic.name)
    page: int = indexed_definition.page

    text = i18n.get("get_term_info").format(
        term=term.name,
        text=definition,
        topic=topic,
        page=page,
    )

    kb = build_books_kb(books=books, book_id=book.id, term_id=term.id, definitions=definitions, current_index=index)

    return text, kb


def get_term_books(
    *,
    term: Term
) -> list[Book]:
    unique = {}

    for definition in term.definitions:
        book = definition.topic.book
        unique[book.id] = book

    return list(unique.values())


def get_term_definitions_in_specific_book(
    *,
    term: Term,
    book: Book,
) -> list[Definition]:
    definitions: list[Definition] = []

    for definition in term.definitions:
        if definition.topic.book_id == book.id:
            definitions.append(definition)

    return definitions
