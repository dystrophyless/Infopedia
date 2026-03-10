import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Definition, Source, Term, Book, Chapter, Topic, TopicCode, TopicMapping


async def load_terms_from_json(session: AsyncSession, embedder, json_path: str):
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    for term_name, sources in data.items():
        query = (
            select(Term)
            .where(Term.name == term_name)
        )
        result = await session.execute(query)

        term: Term = result.scalar_one_or_none()

        if not term:
            term: Term = Term(name=term_name)
            session.add(term)
            await session.flush()

        for source_name, defs in sources.items():
            query = (
                select(Source)
                .where(
                    Source.term_id == term.id,
                    Source.name == source_name,
                )
            )
            result = await session.execute(query)

            source: Source = result.scalar_one_or_none()

            if not source:
                source: Source = Source(name=source_name, term=term)
                session.add(source)
                await session.flush()

            query = (
                select(Book)
                .where(Book.name == source_name)
            )
            result = await session.execute(query)

            book: Book = result.scalar_one_or_none()

            for d in defs:
                query = (
                    select(Topic).where(Topic.name == d["topic"])
                    .where(Topic.book_id == book.id)
                )
                result = await session.execute(query)

                topic: Topic = result.scalar_one_or_none()

                if not topic:
                    raise ValueError(f"Topic '{d["topic"]}' не найден в таблице topics")

                query = (
                    select(Definition)
                    .where(
                        Definition.source_id == source.id,
                        Definition.topic_id == topic.id,
                        Definition.text == d["definition"],
                        Definition.page == d["page"],
                    )
                )
                result = await session.execute(query)

                definition: Definition = result.scalar_one_or_none()

                if not definition:
                    emb = embedder.encode(d["definition"]).tolist()

                    definition: Definition = Definition(
                        text=d["definition"],
                        page=d["page"],
                        topic=topic,
                        source=source,
                        embedding=emb,
                    )
                    session.add(definition)

    await session.commit()


async def load_chapters_and_topic_codes(
    session: AsyncSession,
    json_path: str,
) -> None:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    try:
        for _, chapter_items in data.items():
            for item in chapter_items:
                chapter_name: str = (item.get("title") or "").strip()

                if not chapter_name:
                    continue

                query = (
                    select(Chapter)
                    .where(Chapter.name == chapter_name)
                )
                result = await session.execute(query)

                chapter: Chapter = result.scalar_one_or_none()

                if not chapter:
                    chapter: Chapter = Chapter(name=chapter_name)
                    session.add(chapter)
                    await session.flush()

                for lesson_goal in item.get("lessonGoals", []):
                    topic_code_name: str = (lesson_goal or "").strip()

                    if not topic_code_name:
                        continue

                    query = (
                        select(TopicCode)
                        .where(TopicCode.name == topic_code_name)
                    )
                    result = await session.execute(query)

                    topic_code: TopicCode = result.scalar_one_or_none()

                    if not topic_code:
                        topic_code: TopicCode = TopicCode(
                            name=topic_code_name,
                            chapter_id=chapter.id,
                        )
                        session.add(topic_code)
                        await session.flush()
                    else:
                        if topic_code.chapter_id != chapter.id:
                            raise ValueError(
                                f"TopicCode '{topic_code_name}' уже связан с другим chapter_id="
                                f"{topic_code.chapter_id}, но в JSON встретился в chapter "
                                f"'{chapter_name}' (id={chapter.id})"
                            )

        await session.commit()

    except Exception:
        await session.rollback()
        raise


async def load_books_topics_and_mappings(
    session: AsyncSession,
    json_path: str,
) -> None:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    try:
        for book_name, book_data in data.items():
            query = (
                select(Book)
                .where(Book.name == book_name)
            )
            result = await session.execute(query)

            book: Book = result.scalar_one_or_none()

            if not book:
                book: Book = Book(name=book_name)
                session.add(book)
                await session.flush()

            for topic_item in book_data.get("topics", []):
                topic_name: str = (topic_item.get("title") or "").strip()
                page_start: int = topic_item.get("page_start")
                page_end: int = topic_item.get("page_end")

                if not topic_name:
                    continue

                query = (
                    select(Topic)
                    .where(
                        Topic.book_id == book.id,
                        Topic.name == topic_name,
                    )
                )
                result = await session.execute(query)

                topic: Topic = result.scalar_one_or_none()

                if not topic:
                    topic = Topic(
                        name=topic_name,
                        page_start=page_start,
                        page_end=page_end,
                        book_id=book.id,
                    )
                    session.add(topic)
                    await session.flush()

                code_names_raw = topic_item.get("code_name", [])
                if isinstance(code_names_raw, str):
                    code_names_raw = [code_names_raw]

                for topic_code_name_raw in code_names_raw:
                    topic_code_name = (topic_code_name_raw or "").strip()
                    if not topic_code_name:
                        continue

                    query = (
                        select(TopicCode).where(TopicCode.name == topic_code_name)
                    )
                    result = await session.execute(query)
                    topic_code: TopicCode = result.scalar_one_or_none()

                    if not topic_code:
                        topic_code: TopicCode = TopicCode(
                            name=topic_code_name,
                            chapter_id=None,
                        )
                        session.add(topic_code)
                        await session.flush()

                    query = (
                        select(TopicMapping)
                        .where(
                            TopicMapping.topic_id == topic.id,
                            TopicMapping.topic_code_id == topic_code.id,
                        )
                    )
                    result = await session.execute(query)

                    mapping: TopicMapping = result.scalar_one_or_none()

                    if not mapping:
                        session.add(
                            TopicMapping(
                                topic_id=topic.id,
                                topic_code_id=topic_code.id,
                            )
                        )

        await session.commit()

    except Exception:
        await session.rollback()
        raise
