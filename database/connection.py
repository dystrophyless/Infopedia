import logging
from urllib.parse import quote

from psycopg import AsyncConnection
from psycopg_pool import AsyncConnectionPool


logger = logging.getLogger(__name__)


# Функция, возвращающая безопасную строку `conninfo` для подключения к PostgreSQL
def build_pg_conninfo(
    db_name: str,
    host: str,
    port: int,
    user: str,
    password: str
) -> str:
    conninfo = (
        f"postgresql://{quote(user, safe='')}:{quote(password, safe='')}"
        f"@{host}:{port}/{db_name}"
    )
    logger.debug(f"Строка для подключения PostgreSQL была создана (пароль скрыт): "
                 f"postgresql://{quote(user, safe='')}@{host}:{port}/{db_name}")
    return conninfo
    # conninfo_image = "postgresql://user:password@host:port/db_name"


# Функция, логирующая версию СУБД PostgreSQL, к которой происходит подключение
async def log_db_version(connection: AsyncConnection) -> None:
    try:
        async with connection.cursor() as cursor:
            await cursor.execute("SELECT version();")
            db_version = await cursor.fetchone()
            logger.debug(f"Версия PostgreSQL к которой было сделано подключение: {db_version[0]}")
    except Exception as e:
        logger.exception(f"Не удалось получить версию PostgreSQL: %s", e)



# Функция, возвращающая открытое соединение с СУБД PostgreSQL
async def get_pg_connection(
    db_name: str,
    host: str,
    port: int,
    user: str,
    password: str
) -> AsyncConnection:
    conninfo = build_pg_conninfo(db_name, host, port, user, password)
    connection: AsyncConnection | None = None

    try:
        connection = await AsyncConnection.connect(conninfo=conninfo)
        await log_db_version(connection)
        return connection
    except Exception as e:
        logger.exception(f"Не удалось подключиться к PostgreSQL: %s", e)
        if connection:
            await connection.close()
        raise


# Функция, возвращающая пул соединений с СУБД PostgreSQL
async def get_pg_pool(
    db_name: str,
    host: str,
    port: int,
    user: str,
    password: str,
    min_size: int = 1,
    max_size: int = 3,
    timeout: float | None = 10.0
) -> AsyncConnectionPool:
    conninfo = build_pg_conninfo(db_name, host, port, user, password)
    db_pool: AsyncConnectionPool | None = None

    try:
        db_pool = AsyncConnectionPool(
            conninfo=conninfo,
            min_size=min_size,
            max_size=max_size,
            timeout=timeout,
            open=False
        )

        await db_pool.open()

        async with db_pool.connection() as connection:
            await log_db_version(connection)

        return db_pool
    except Exception as e:
        logger.exception("Не удалось осуществить подключение к пулу соединений PostgreSQL: %s", e)
        if db_pool and not db_pool.closed:
            await db_pool.close()
        raise