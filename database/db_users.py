import logging

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Activity, Users
from enums.grades import UserGrade
from enums.roles import UserRole

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
    banned: bool = False,
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
        banned,
    )


async def get_user(
    session: AsyncSession,
    *,
    user_id: int
) -> Users | None:
    query = (
        select(Users)
        .where(Users.user_id == user_id)
    )
    result = await session.execute(query)

    user = result.scalar_one_or_none()

    if user is None:
        logger.debug(
            "Не удалось получить пользователя с `user_id`='%s' из базы данных",
            user_id,
        )
        return None

    logger.debug("Получили данные для пользователя с `user_id`='%d'", user_id)

    return user


async def change_user_alive_status(
    session: AsyncSession,
    *,
    is_alive: bool,
    user_id: int,
) -> None:
    stmt = (
        update(Users)
        .where(Users.user_id == user_id)
        .values(is_alive=is_alive)
    )
    result = await session.execute(stmt)

    is_alive_in_db = result.scalar_one_or_none()

    if is_alive_in_db is None:
        logger.debug(
            "Не удалось получить пользователя с `user_id`='%s' из базы данных",
            user_id,
        )
        return

    logger.debug(
        "Обновлён статус `is_alive` на '%s' для пользователя с `user_id`='%d'",
        is_alive,
        user_id,
    )


async def change_user_banned_status_by_id(
    session: AsyncSession,
    *,
    banned: bool,
    user_id: int,
) -> None:
    stmt = (
        update(Users)
        .where(Users.user_id == user_id)
        .values(banned=banned)
    )
    result = await session.execute(stmt)

    is_banned_in_db = result.scalar_one_or_none()

    if is_banned_in_db is None:
        logger.debug(
            "Не удалось получить пользователя с `user_id`='%s' из базы данных",
            user_id,
        )
        return

    logger.debug(
        "Обновлён статус `banned` на '%s' для пользователя с `user_id`='%d'",
        banned,
        user_id,
    )


async def change_user_banned_status_by_username(
    session: AsyncSession,
    *,
    banned: bool,
    username: str,
) -> None:
    stmt = (
        update(Users)
        .where(Users.username == username)
        .values(banned=banned)
    )
    result = await session.execute(stmt)

    is_banned = result.scalar_one_or_none()

    if is_banned is None:
        logger.debug(
            "Не удалось получить пользователя с `username`='%s' из базы данных",
            username,
        )
        return

    logger.debug(
        "Обновлён статус `banned` на '%s' для пользователя с `username`='%s'",
        banned,
        username,
    )


async def update_user_language(
    session: AsyncSession,
    *,
    language: str,
    user_id: int,
) -> None:
    stmt = (
        update(Users)
        .where(Users.user_id == user_id)
        .values(language=language)
        .returning(Users.user_id)
    )
    result = await session.execute(stmt)

    updated_user_id: int = result.scalar_one_or_none()

    if updated_user_id is None:
        logger.debug("Попытка обновить язык несуществующему пользователю: %d", user_id)
        return

    logger.debug(
        "Язык `language`='%s' был установлен для пользователя с `user_id`='%d'",
        language,
        user_id,
    )


async def get_user_language(session: AsyncSession, *, user_id: int) -> str | None:
    query = (
        select(Users.language)
        .where(Users.user_id == user_id)
    )
    result = await session.execute(query)

    language: str = result.scalar_one_or_none()

    if language is None:
        logger.debug(
            "Не удалось получить пользователя с `user_id`='%s' из базы данных",
            user_id,
        )
        return None

    logger.debug(
        "У пользователя с `user_id`='%d' установлен следующий язык `language`='%s'",
        user_id,
        language,
    )

    return language


async def get_user_alive_status(session: AsyncSession, *, user_id: int) -> bool | None:
    query = (
        select(Users.is_alive)
        .where(Users.user_id == user_id)
    )
    result = await session.execute(query)

    is_alive: bool = result.scalar_one_or_none()

    if is_alive is None:
        logger.debug(
            "Не удалось получить пользователя с `user_id`='%s' из базы данных",
            user_id,
        )
        return None

    logger.debug(
        "У пользователя с `user_id`='%d' установлен следующий статус `is_alive`='%s'",
        user_id,
        is_alive,
    )

    return is_alive


async def get_user_banned_status_by_id(
    session: AsyncSession,
    *,
    user_id: int,
) -> bool | None:
    query = (
        select(Users.banned)
        .where(Users.user_id == user_id)
    )
    result = await session.execute(query)

    banned: bool = result.scalar_one_or_none()

    if banned is None:
        logger.debug(
            "Не удалось получить пользователя с `user_id`='%s' из базы данных",
            user_id,
        )
        return None

    logger.debug(
        "У пользователя с `user_id`='%d' установлен следующий статус `banned`='%s'",
        user_id,
        banned,
    )

    return banned


async def get_user_banned_status_by_username(
    session: AsyncSession,
    *,
    username: str,
) -> bool | None:
    query = (
        select(Users.banned)
        .where(Users.username == username)
    )
    result = await session.execute(query)

    banned: bool = result.scalar_one_or_none()

    if banned is None:
        logger.debug(
            "Не удалось получить пользователя с `username`='%s' из базы данных",
            username,
        )
        return None

    logger.debug(
        "У пользователя с `username`='%s' установлен следующий статус `banned`='%s'",
        username,
        banned,
    )

    return banned


async def get_user_role(session: AsyncSession, *, user_id: int) -> UserRole | None:
    query = (
        select(Users.role).where(Users.user_id == user_id)
    )
    result = await session.execute(query)

    role: UserRole = result.scalar_one_or_none()

    if role is None:
        logger.debug(
            "Не удалось получить пользователя с `user_id`='%s' из базы данных",
            user_id,
        )
        return None

    logger.debug(
        "У пользователя с `user_id`='%s' установлена следующая роль: %s",
        user_id,
        role,
    )

    return role


async def get_user_grade(session: AsyncSession, *, user_id: int) -> UserGrade | None:
    query = (
        select(Users.grade)
        .where(Users.user_id == user_id)
    )
    result = await session.execute(query)

    grade: UserGrade = result.scalar_one_or_none()

    if grade is None:
        logger.debug(
            "Не удалось получить пользователя с `user_id`='%s' из базы данных",
            user_id,
        )
        return None

    logger.debug(
        "У пользователя с `user_id`='%s' установлена следующий класс: %s",
        user_id,
        grade,
    )

    return grade


async def add_user_activity(session: AsyncSession, *, user_id: int) -> None:
    stmt = (
        insert(Activity)
        .values(user_id=user_id)
        .on_conflict_do_update(
            index_elements=["user_id", "activity_date"],
            set_={"actions": Activity.actions + 1},
        )
    )
    await session.execute(stmt)
    logger.debug(
        "Активность пользователя с `user_id`='%d' была обновлена в таблице `activity`",
        user_id,
    )
