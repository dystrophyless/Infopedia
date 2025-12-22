import logging

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import async_sessionmaker,AsyncSession
from sqlalchemy.dialects.postgresql import insert

from database.models import Users, Activity
from enums.roles import UserRole
from enums.grades import UserGrade


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
