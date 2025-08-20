import logging
from datetime import datetime, timezone
from typing import Any
from psycopg import AsyncConnection

from enums.roles import UserRole


logger = logging.getLogger(__name__)


async def add_user(
    conn: AsyncConnection,
    *,
    user_id: int,
    username: str | None = None,
    language: str = "ru",
    grade: str = "undefined",
    role: UserRole = UserRole.USER,
    is_alive: bool = True,
    banned: bool = False
) -> None:
    async with conn.cursor() as cursor:
        await cursor.execute(
            query="""
                INSERT INTO users(user_id, username, language, grade, role, is_alive, banned)
                VALUES(
                    %(user_id)s,
                    %(username)s,
                    %(language)s,
                    %(grade)s,
                    %(role)s,
                    %(is_alive)s,
                    %(banned)s
                ) ON CONFLICT DO NOTHING;
            """,
            params={
                "user_id": user_id,
                "username": username,
                "language": language,
                "grade": grade,
                "role": role,
                "is_alive": is_alive,
                "banned": banned,
            }
        )

    logger.debug(
        "Пользователь был добавлен в базу данных. "
        "`user_id`='%d', `created_at`='%s', `language`='%s', `grade`='%s', `followed_after_bot`='%s', `is_alive`='%s',  `banned`='%s'",
        user_id,
        datetime.now(timezone.utc),
        language,
        grade,
        is_alive,
        banned
    )


async def get_user(
    conn: AsyncConnection,
    *,
    user_id: int
) -> tuple[Any, ...] | None:
    async with conn.cursor() as cursor:
        data = await cursor.execute(
            query="""
                SELECT
                    id,
                    user_id,
                    username,
                    language,
                    grade,
                    role,
                    is_alive,
                    banned
                FROM users WHERE user_id=%(user_id)s;
            """,
            params={
                "user_id": user_id,
            }
        )
        row = await data.fetchone()
    logger.debug("Строка: '%s'", row)
    return row if row else None


async def change_user_alive_status(
    conn: AsyncConnection,
    *,
    is_alive: bool,
    user_id: int
) -> None:
    async with conn.cursor() as cursor:
        await cursor.execute(
            query="""
                UPDATE users
                SET is_alive=%(is_alive)s
                WHERE user_id=%(user_id)s;
            """,
            params={
                "is_alive": is_alive,
                "user_id": user_id
            }
        )
    logger.debug("Обновлён статус `is_alive` на '%s' для пользователя с `user_id`='%d'", is_alive, user_id)


async def change_user_banned_status_by_id(
    conn: AsyncConnection,
    *,
    banned: bool,
    user_id: int
) -> None:
    async with conn.cursor() as cursor:
        await cursor.execute(
            query="""
                UPDATE users
                SET banned=%(banned)s
                WHERE user_id=%(user_id)s;
            """,
            params={
                "banned": banned,
                "user_id": user_id
            }
        )
    logger.debug("Обновлён статус `banned` на '%s' для пользователя с `user_id`='%d'", banned, user_id)


async def change_user_banned_status_by_username(
    conn: AsyncConnection,
    *,
    banned: bool,
    username: str
) -> None:
    async with conn.cursor() as cursor:
        await cursor.execute(
            query="""
                UPDATE users
                SET banned=%(banned)s
                WHERE username=%(username)s;
            """,
            params={
                "banned": banned,
                "username": username
            }
        )
    logger.debug("Обновлён статус `banned` на '%s' для пользователя с `username`='%s'", banned, username)


async def update_user_language(
    conn: AsyncConnection,
    *,
    language: str,
    user_id: int
) -> None:
    async with conn.cursor() as cursor:
        await cursor.execute(
            query="""
                UPDATE users
                SET language=%(language)s
                WHERE user_id=%(user_id)s;
            """,
            params={
                "language": language,
                "user_id": user_id
            }
        )
    logger.debug("Язык `language`='%s' был установлен для пользователя с `user_id`='%d'", language, user_id)


async def get_user_language(
    conn: AsyncConnection,
    *,
    user_id: int
) -> str | None:
    async with conn.cursor() as cursor:
        data = await cursor.execute(
            query="""
                SELECT language
                FROM users
                WHERE user_id=%(user_id)s;
            """,
            params={
                "user_id": user_id
            }
        )
        row = await data.fetchone()
    if row:
        logger.debug("У пользователя с `user_id`='%d' установлен следующий язык `language`='%s'", user_id, row[0])
    else:
        logger.warning("Не найден пользователь с `user_id`='%d' в базе данных", user_id)
    return row[0] if row else None


async def get_user_alive_status(
    conn: AsyncConnection,
    *,
    user_id: int
) -> bool | None:
    async with conn.cursor() as cursor:
        data = await cursor.execute(
            query="""
                SELECT is_alive
                FROM users
                WHERE user_id=%(user_id)s;
            """,
            params={
                "user_id": user_id
            }
        )
        row = await data.fetchone()
    if row:
        logger.debug("У пользователя с `user_id`='%d' установлен следующий статус `is_alive`='%s'", user_id, row[0])
    else:
        logger.warning("Не найден пользователь с `user_id`=%s в базе данных", user_id)
    return row[0] if row else None


async def get_user_banned_status_by_id(
    conn: AsyncConnection,
    *,
    user_id: int
) -> bool | None:
    async with conn.cursor() as cursor:
        data = await cursor.execute(
            query="""
                SELECT banned
                FROM users
                WHERE user_id=%(user_id)s;
            """,
            params={
                "user_id": user_id
            }
        )
        row = await data.fetchone()
    if row:
        logger.debug("У пользователя с `user_id`='%d' установлен следующий статус `banned`='%s'", user_id, row[0])
    else:
        logger.warning("Не найден пользователь с `user_id`='%d' в базе данных", user_id)
    return row[0] if row else None


async def get_user_banned_status_by_username(
    conn: AsyncConnection,
    *,
    username: str
) -> bool | None:
    async with conn.cursor() as cursor:
        data = await cursor.execute(
            query="""
                SELECT banned
                FROM users
                WHERE username=%(username)s;
            """,
            params={
                "username": username
            }
        )
        row = await data.fetchone()
    if row:
        logger.debug("У пользователя с `username`='%s' установлен следующий статус `banned`='%s'", username, row[0])
    else:
        logger.warning("Не найден пользователь с `username`='%s' в базе данных", username)
    return row[0] if row else None


async def get_user_role(
    conn: AsyncConnection,
    *,
    user_id: int
) -> UserRole | None:
    async with conn.cursor() as cursor:
        data = await cursor.execute(
            query="""
                SELECT role
                FROM users
                WHERE user_id=%(user_id)s;
            """,
            params={
                "user_id": user_id
            }
        )
        row = await data.fetchone()
    if row:
        logger.debug("У пользователя с `user_id`='%s' установлена следующая роль: %s", user_id, row[0])
    else:
        logger.warning("Не найден пользователь с `user_id`=%s в базе данных", user_id)
    return UserRole(row[0]) if row else None


async def add_user_activity(
    conn: AsyncConnection,
    *,
    user_id: int
) -> None:
    async with conn.cursor() as cursor:
        await cursor.execute(
            query="""
                INSERT INTO activity (user_id)
                VALUES (%(user_id)s)
                ON CONFLICT (user_id, activity_date)
                DO UPDATE
                SET actions = activity.actions + 1;
            """,
            params={
                "user_id": user_id
            }
        )
    logger.debug("Активность пользователя с `user_id`='%d' была обновлена в таблице `activity`", user_id)


async def get_statistics(conn: AsyncConnection) -> list[Any, ...] | None:
    async with conn.cursor() as cursor:
        data = await cursor.execute(
            query="""
                SELECT user_id, SUM(actions) AS total_actions
                FROM activity
                GROUP BY user_id
                ORDER BY total_actions DESC
                LIMIT 5;
            """
        )
        rows = await data.fetchall()
    logger.debug("Была получена статистика активности пользователей с таблицы `activity`")
    return [*rows] if rows else None