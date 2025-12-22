from sqlalchemy import select
from sqlalchemy.orm import selectinload
from database.models import Definition, Source

async def get_definition_candidates(session, qvec_list, top_k: int):
    stmt = (
        select(
            Definition,
            (1 - Definition.embedding.cosine_distance(qvec_list)).label("sim_approx")
        )
        .options(selectinload(Definition.source).selectinload(Source.term))
        .order_by(Definition.embedding.cosine_distance(qvec_list))
        .limit(top_k)
    )
    result = await session.execute(stmt)
    return result.all()