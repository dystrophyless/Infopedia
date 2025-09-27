import logging
import numpy as np

from sqlalchemy import func, select, case, Float, Integer
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from sqlalchemy.dialects.postgresql import insert

from sentence_transformers import SentenceTransformer, CrossEncoder

from database.models import Users, Activity, Term, Source, Definition, UserFeedback
from enums.roles import UserRole
from enums.grades import UserGrade
from schemas.user import UserStat
from schemas.feedback import FeedbackStat


logger = logging.getLogger(__name__)


async def add_user(
    session: AsyncSession,
    *,
    user_id: int,
    username: str | None = None,
    first_name: str,
    language: str = "ru",
    grade: UserGrade = UserGrade.GRADE_UNDEFINED,
    role: UserRole = UserRole.USER,
    is_alive: bool = True,
    banned: bool = False
) -> None:
    new_user: Users = Users(
        user_id=user_id,
        username=username,
        first_name=first_name,
        language=language,
        grade=grade,
        role=role,
        is_alive=is_alive,
        banned=banned,
    )
    session.add(new_user)

    logger.debug(
        "Пользователь был добавлен в базу данных."
        "user_id='%d', `first_name`='%s', `language`='%s', `grade`='%s', `role`='%s', `is_alive`='%s', `banned`='%s'",
        user_id,
        first_name,
        language,
        grade,
        role,
        is_alive,
        banned
    )


async def get_user(
    session: AsyncSession,
    *,
    user_id: int
) -> Users | None:
    result = await session.execute(
        select(Users)
        .filter_by(user_id=user_id)
    )

    user = result.scalar_one_or_none()

    return user


async def change_user_alive_status(
    session: AsyncSession,
    *,
    is_alive: bool,
    user_id: int
) -> None:
    result = await session.execute(
        select(Users)
        .filter_by(user_id=user_id)
    )

    user = result.scalar_one_or_none()

    if user is None:
        logger.debug("Не удалось получить пользователя с `user_id`='%s' из базы данных", user_id)
        return

    user.is_alive = is_alive

    logger.debug("Обновлён статус `is_alive` на '%s' для пользователя с `user_id`='%d'", is_alive, user_id)


async def change_user_banned_status_by_id(
    session: AsyncSession,
    *,
    banned: bool,
    user_id: int
) -> None:
    result = await session.execute(
        select(Users)
        .filter_by(user_id=user_id)
    )

    user = result.scalar_one_or_none()

    if user is None:
        logger.debug("Не удалось получить пользователя с `user_id`='%s' из базы данных", user_id)
        return

    user.banned = banned

    logger.debug("Обновлён статус `banned` на '%s' для пользователя с `user_id`='%d'", banned, user_id)


async def change_user_banned_status_by_username(
    session: AsyncSession,
    *,
    banned: bool,
    username: str
) -> None:
    result = await session.execute(
        select(Users)
        .filter_by(username=username)
    )

    user = result.scalar_one_or_none()

    if user is None:
        logger.debug("Не удалось получить пользователя с `username`='%s' из базы данных", username)
        return

    user.banned = banned

    logger.debug("Обновлён статус `banned` на '%s' для пользователя с `username`='%s'", banned, username)


async def update_user_language(
    session: AsyncSession,
    *,
    language: str,
    user_id: int
) -> None:
    result = await session.execute(
        select(Users)
        .filter_by(user_id=user_id)
    )

    user = result.scalar_one_or_none()

    if user is None:
        logger.debug("Не удалось получить пользователя с `user_id`='%s' из базы данных", user_id)
        return

    user.language = language

    logger.debug("Язык `language`='%s' был установлен для пользователя с `user_id`='%d'", language, user_id)


async def get_user_language(
    session: AsyncSession,
    *,
    user_id: int
) -> str | None:
    result = await session.execute(
        select(Users)
        .filter_by(user_id=user_id)
    )

    user = result.scalar_one_or_none()

    if user is None:
        logger.debug("Не удалось получить пользователя с `user_id`='%s' из базы данных", user_id)
        return None

    language: str = user.language

    logger.debug("У пользователя с `user_id`='%d' установлен следующий язык `language`='%s'", user_id, language)

    return language


async def get_user_alive_status(
    session: AsyncSession,
    *,
    user_id: int
) -> bool | None:
    result = await session.execute(
        select(Users)
        .filter_by(user_id=user_id)
    )

    user = result.scalar_one_or_none()

    if user is None:
        logger.debug("Не удалось получить пользователя с `user_id`='%s' из базы данных", user_id)
        return None

    is_alive: bool = user.is_alive

    logger.debug("У пользователя с `user_id`='%d' установлен следующий статус `is_alive`='%s'", user_id, is_alive)

    return is_alive


async def get_user_banned_status_by_id(
    session: AsyncSession,
    *,
    user_id: int
) -> bool | None:
    result = await session.execute(
        select(Users)
        .filter_by(user_id=user_id)
    )

    user = result.scalar_one_or_none()

    if user is None:
        logger.debug("Не удалось получить пользователя с `user_id`='%s' из базы данных", user_id)
        return None

    banned: bool = user.banned

    logger.debug("У пользователя с `user_id`='%d' установлен следующий статус `banned`='%s'", user_id, banned)

    return banned


async def get_user_banned_status_by_username(
    session: AsyncSession,
    *,
    username: str
) -> bool | None:
    result = await session.execute(
        select(Users)
        .filter_by(username=username)
    )

    user = result.scalar_one_or_none()

    if user is None:
        logger.debug("Не удалось получить пользователя с `username`='%s' из базы данных", username)
        return None


    banned: bool = user.banned

    logger.debug("У пользователя с `username`='%s' установлен следующий статус `banned`='%s'", username, banned)

    return banned


async def get_user_role(
    session: AsyncSession,
    *,
    user_id: int
) -> UserRole | None:
    result = await session.execute(
        select(Users).
        filter_by(user_id=user_id)
    )

    user = result.scalar_one_or_none()

    if user is None:
        logger.debug("Не удалось получить пользователя с `user_id`='%s' из базы данных", user_id)
        return None

    role: str = user.role

    logger.debug("У пользователя с `user_id`='%s' установлена следующая роль: %s", user_id, role)

    return UserRole(role)


async def get_user_grade(
    session: AsyncSession,
    *,
    user_id: int
) -> UserGrade | None:
    result = await session.execute(
        select(Users)
        .filter_by(user_id=user_id)
    )

    user = result.scalar_one_or_none()

    if user is None:
        logger.debug("Не удалось получить пользователя с `user_id`='%s' из базы данных", user_id)
        return None

    grade: str = user.grade

    logger.debug("У пользователя с `user_id`='%s' установлена следующий класс: %s", user_id, grade)

    return UserGrade(grade)

async def add_user_activity(
    session: AsyncSession,
    *,
    user_id: int
) -> None:
    stmt = insert(Activity).values(user_id=user_id).on_conflict_do_update(
        index_elements=["user_id", "activity_date"],
        set_={"actions": Activity.actions + 1}
    )
    await session.execute(stmt)
    logger.debug("Активность пользователя с `user_id`='%d' была обновлена в таблице `activity`", user_id)


async def get_activity_statistics_individually(session: AsyncSession) -> list[UserStat] | None:
    query = (
        select(
            Activity.user_id,
            func.sum(Activity.actions),
            Users.username,
            Users.first_name,
        )
        .join(Users, Users.user_id == Activity.user_id)
        .group_by(Activity.user_id, Users.username, Users.first_name)
        .order_by(func.sum(Activity.actions).desc())
        .limit(5)
    )

    result = await session.execute(query)

    rows = result.all()

    if not rows:
        logger.debug("Не удалось получить статистику активности пользователей из базы данных")
        return None

    statistics: list[UserStat] = [
        UserStat(
            user_id=user_id,
            username=username,
            first_name=first_name,
            total_actions=total_actions
        )
        for user_id, total_actions, username, first_name in rows
    ]

    logger.debug("Была получена статистика активности пользователей с таблицы `activity`")
    return statistics


async def get_activity_statistics_generally(session: AsyncSession) -> int | None:
    query = (
        select(func.sum(Activity.actions))
    )

    result = await session.execute(query)

    total_actions: int = result.scalar_one_or_none()

    if total_actions is None:
        logger.debug("Не удалось получить общее количество действий выполненными всеми пользователями за сегодня")
        return None

    return total_actions


async def add_search_feedback(
    session: AsyncSession,
    *,
    user_id: int,
    definition_id: int,
    query: str,
    correct: bool
) -> None:
    new_feedback: UserFeedback = UserFeedback(
        user_id=user_id,
        definition_id=definition_id,
        query=query,
        correct=correct
    )

    session.add(new_feedback)

    logger.debug(
        "Фидбэк по поиску по определению был добавлен в базу данных. "
        "user_id='%d', `definition_id`='%d', `query`='%s', `correct`='%s'",
        user_id,
        definition_id,
        query,
        correct,
    )


async def get_search_statistics_individually(session: AsyncSession, limit: int = 10) -> list[FeedbackStat] | None:
    query = (
        select(
            Definition.id,
            Term.name,
            func.count(UserFeedback.id),
            func.sum(case((UserFeedback.correct == True, 1), else_=0)),
            (
                (func.sum(case((UserFeedback.correct == True, 1), else_=0)).cast(Float) / func.count(UserFeedback.id).cast(Float) * 100).cast(Integer)
            ).label("accuracy")
        )
        .join(UserFeedback, UserFeedback.definition_id == Definition.id)
        .join(Source, Source.id == Definition.source_id)
        .join(Term, Term.id == Source.term_id)
        .group_by(Definition.id, Term.name)
        .having(
            (func.sum(case((UserFeedback.correct == True, 1), else_=0)) / func.count(UserFeedback.id) * 100) <= 70
        )
        .order_by("accuracy")
        .limit(limit)
    )

    result = await session.execute(query)
    rows = result.all()

    if not rows:
        logger.debug("Не удалось получить индивидуальную статистику точности поиска по определению из базы данных")
        return None

    statistics: list[FeedbackStat] = [
        FeedbackStat(
            definition_id=definition_id,
            term_name=term_name,
            total_queries=total_queries,
            correct_queries=correct_queries,
            accuracy=accuracy
        )
        for definition_id, term_name, total_queries, correct_queries, accuracy in rows
    ]

    logger.debug("Была получена индивидуальная статистика точности поиска по определению из базы данных")
    return statistics


async def get_search_statistics_generally(session: AsyncSession) -> tuple[int, int] | None:
    query = (
        select(
            func.count(UserFeedback.id),
            (
                (func.sum(case((UserFeedback.correct == True, 1), else_=0)).cast(Float) / func.count(UserFeedback.id).cast(Float) * 100).cast(Integer)
            ).label("accuracy")
        )
    )

    result = await session.execute(query)
    rows = result.one_or_none()

    if not rows:
        logger.debug("Не удалось получить общую статистику точности поиска по определению из базы данных")
        return None

    total_queries, accuracy = rows

    return total_queries, accuracy


async def get_total_users(sessionmaker: async_sessionmaker[AsyncSession]) -> int | None:
    async with sessionmaker() as session:
        try:
            async with session.begin():
                result = await session.execute(select(func.count(Users.id)))

                total_users_count: int = result.scalar_one_or_none()

                return total_users_count
        except Exception as e:
            logger.exception("Транзакция откатилась из-за ошибки: %s", e)
            raise


async def get_total_terms(sessionmaker: async_sessionmaker[AsyncSession]) -> int | None:
    async with sessionmaker() as session:
        try:
            async with session.begin():
                result = await session.execute(select(func.count(Term.id)))

                total_terms_count: int = result.scalar_one_or_none()

                return total_terms_count
        except Exception as e:
            logger.exception("Транзакция откатилась из-за ошибки: %s", e)
            raise


async def get_term_by_name(
    session: AsyncSession,
    *,
    name: str
) -> Term | None:
    result = await session.execute(select(Term).filter_by(name=name))

    if result is None:
        logger.debug("Не удалось получить термин с `name`='%s' из базы данных", name)
        return None

    term: Term = result.scalar_one_or_none()

    return term


async def get_term_by_id(
    session: AsyncSession,
    *,
    id: int
) -> Term | None:
    result = await session.execute(
        select(Term)
        .filter_by(id=id)
    )

    if result is None:
        logger.debug("Не удалось получить термин с `id`='%s' из базы данных", id)
        return None

    term: Term = result.scalar_one_or_none()

    return term


async def get_source_by_id(
    session: AsyncSession,
    *,
    id: int
) -> Source | None:
    result = await session.execute(
        select(Source)
        .filter_by(id=id)
    )

    if result is None:
        logger.debug("Не удалось получить источник с `id`='%s' из базы данных", id)
        return None

    source: Source = result.scalar_one_or_none()

    return source

async def get_random_terms(
    session: AsyncSession,
    *,
    quantity: int
) -> list[Term] | None:
    result = await session.execute(
        select(Term)
        .order_by(func.random())
        .limit(quantity)
    )

    if result is None:
        logger.debug("Не удалось получить рандомные термины из базы данных")
        return None

    terms: list[Term] = list(result.scalars().all())

    return terms


async def search_terms_by_prefix(
    session: AsyncSession,
    *,
    query: str,
    limit: int = 10,
    prefix: bool = True
) -> list[Term] | None:

    like: str = f"{query}%" if prefix else f"%{query}%"
    result = await session.execute(
        select(Term)
        .where(Term.name.ilike(like))
        .limit(limit)
    )

    if result is None:
        logger.debug("Не удалось получить термины которые начинаются на `query=%s` из базы данных", query)
        return None

    terms: list[Term] = list(result.scalars().all())

    return terms


async def search_terms_by_similarity(
    session: AsyncSession,
    *,
    query: str,
    limit: int = 10,
) -> list[Term] | None:
    result = await session.execute(
        select(Term)
        .where(Term.name.op("%")(query))
        .order_by(func.similarity(Term.name, query).desc())
        .limit(limit)
    )

    if result is None:
        logger.debug("Не удалось получить термины похожие на `query=%s` из базы данных", query)
        return None

    terms: list[Term] = list(result.scalars().all())

    return terms


async def get_closest_definition(
    session: AsyncSession,
    embedder: SentenceTransformer,
    reranker: CrossEncoder,
    *,
    query: str,
    top_k: int = 10,
    similarity_threshold: float = 0.72,
) -> Definition | None:
    try:
        qvec = embedder.encode(query, convert_to_numpy=True)
    except Exception as e:
        logger.exception("Ошибка при получении эмбеддинга для запроса: %r", query)
        return None

    qvec = np.asarray(qvec).ravel()
    qnorm = np.linalg.norm(qvec)
    if qnorm == 0 or np.isnan(qnorm):
        logger.debug("Невалидный/нулевой вектор для запроса: %r", query)
        return None
    qvec = qvec / qnorm
    qvec_list = qvec.tolist()

    stmt = (
        select(
            Definition,
            (1 - Definition.embedding.cosine_distance(qvec_list)).label("sim_approx"),
        )
        .options(
            selectinload(Definition.source).selectinload(Source.term)  # правильно: через Source.term
        )
        .order_by(Definition.embedding.cosine_distance(qvec_list))
        .limit(top_k)
    )

    try:
        result = await session.execute(stmt)
    except Exception:
        logger.exception("Ошибка при выполнении SQL-запроса поиска кандидатов.")
        return None

    rows = result.all()
    if not rows:
        logger.debug("Кандидаты не найдены (top_k=%d) для запроса: %r", top_k, query)
        return None

    logger.debug("Получили следующий запрос: %s. Сравниваем кандидатов", query)

    candidates = []
    for row in rows:
        definition = row[0]
        sim_approx = None
        try:
            sim_approx = float(row[1]) if row[1] is not None else None
        except Exception:
            sim_approx = None

        emb_raw = definition.embedding
        if emb_raw is None:
            logger.debug("Пропускаем id=%s: embedding is None", getattr(definition, "id", "?"))
            continue

        emb = np.asarray(emb_raw, dtype=float).ravel()
        if emb.size == 0:
            logger.debug("Пропускаем id=%s: пустой embedding", getattr(definition, "id", "?"))
            continue

        emb_norm = np.linalg.norm(emb)
        if emb_norm == 0 or np.isnan(emb_norm):
            logger.debug("Пропускаем id=%s: невалидный эмбеддинг (norm=0/NaN)", getattr(definition, "id", "?"))
            continue

        emb = emb / emb_norm
        exact_sim = float(np.dot(qvec, emb))
        candidates.append((definition, sim_approx, exact_sim))

    if not candidates:
        logger.debug("После фильтрации кандидатов не осталось ни одного валидного эмбеддинга.")
        return None

    texts = [d.text for d, _, _ in candidates]
    pairs = [(query, t) for t in texts]
    rerank_scores = reranker.predict(pairs)  # numpy array

    candidates_with_rerank = [
        (definition, sim_approx, exact_sim, float(rerank_score))
        for (definition, sim_approx, exact_sim), rerank_score in zip(candidates, rerank_scores)
    ]


    candidates_sorted = sorted(candidates_with_rerank, key=lambda t: t[3], reverse=True)
    logger.debug("Найдено %d кандидатов (`top_k`='%d'). Листинг (approx -> exact):", len(candidates_sorted), top_k)
    for idx, (d, sim_approx, exact_sim, rerank_score) in enumerate(candidates_sorted, start=1):
        term_name = "<no_term>"
        try:
            term_name = d.source.term.name if (d.source is not None and d.source.term is not None) else "<no_term>"
        except Exception:
            term_name = "<no_term>"

        src_name = getattr(d.source, "name", "<no_source>")
        def_id = getattr(d, "id", "?")
        text_snip = (d.text.replace("\n", " ")[:120] + "...") if len(d.text) > 120 else d.text.replace("\n", " ")
        logger.debug(
            "  #%02d: `id`='%s', `term`='%s', `source`='%s', `approx`='%s', `exact`='%.4f', `rerank`='%.4f', `snippet`='%s'",
            idx,
            def_id,
            term_name,
            src_name,
            f"{sim_approx:.4f}" if sim_approx is not None else "None",
            exact_sim,
            rerank_score,
            text_snip,
        )

    best_def, best_approx, best_sim, best_rerank = candidates_sorted[0]
    logger.debug("Лучший кандидат: `id`='%s', `term`='%s', `exact_sim`='%.4f', `rerank`='%.4f', (`threshold`='%.3f')",
                 getattr(best_def, "id", "?"),
                 (best_def.source.term.name if (best_def.source and best_def.source.term) else "<no_term>"),
                 best_sim,
                 best_rerank,
                 similarity_threshold)

    if best_rerank < similarity_threshold:
        logger.debug("Лучший кандидат ниже порога (%.4f < %.4f). Возвращаем None.", best_sim, similarity_threshold)
        return None

    return best_def


