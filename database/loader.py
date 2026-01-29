import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Definition, Source, Term


async def load_terms_from_json(session: AsyncSession, embedder, json_path: str):
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    for term_name, sources in data.items():
        result = await session.execute(select(Term).where(Term.name == term_name))
        term = result.scalar_one_or_none()

        if not term:
            term = Term(name=term_name)
            session.add(term)
            await session.flush()

        for source_name, defs in sources.items():
            result = await session.execute(
                select(Source).where(
                    Source.term_id == term.id,
                    Source.name == source_name,
                ),
            )
            source = result.scalar_one_or_none()

            if not source:
                source = Source(name=source_name, term=term)
                session.add(source)
                await session.flush()

            for d in defs:
                result = await session.execute(
                    select(Definition).where(
                        Definition.source_id == source.id,
                        Definition.text == d["definition"],
                        Definition.topic == d.get("topic"),
                        Definition.page == d.get("page"),
                    ),
                )
                definition = result.scalar_one_or_none()

                if not definition:
                    emb = embedder.encode(d["definition"]).tolist()

                    definition = Definition(
                        text=d["definition"],
                        topic=d.get("topic"),
                        page=d.get("page"),
                        source=source,
                        embedding=emb,
                    )
                    session.add(definition)

    await session.commit()
