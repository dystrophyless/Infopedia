import logging
from urllib.parse import quote

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

logger = logging.getLogger(__name__)


def build_pg_conninfo(
    db_name: str,
    host: str,
    port: int,
    user: str,
    password: str,
) -> str:
    conninfo = (
        f"postgresql+psycopg://{quote(user, safe='')}:{quote(password, safe='')}"
        f"@{host}:{port}/{db_name}"
    )
    logger.debug(
        "Строка для подключения PostgreSQL была создана (пароль скрыт): "
        f"postgresql+psycopg://{quote(user, safe='')}@{host}:{port}/{db_name}"
    )
    return conninfo


async def log_db_version(engine: AsyncEngine) -> None:
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version();"))
            db_version = result.scalar_one()
            logger.debug(f"Версия PostgreSQL: {db_version}")
    except Exception as e:
        logger.exception("Не удалось получить версию PostgreSQL: %s", e)


def get_async_engine(
    db_name: str,
    host: str,
    port: int,
    user: str,
    password: str,
    echo: bool = False,
    pool_size: int = 5,
    max_overflow: int = 10,
) -> AsyncEngine:
    conninfo = build_pg_conninfo(db_name, host, port, user, password)
    engine = create_async_engine(
        conninfo,
        echo=echo,
        pool_size=pool_size,
        max_overflow=max_overflow,
    )
    return engine


def get_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
        autoflush=False,
    )


async def init_similarity_extension(engine: AsyncEngine):
    try:
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))
            await conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_terms_name_trgm ON terms USING gin (name gin_trgm_ops);"
                )
            )
    except Exception as e:
        logger.exception(
            "Не удалось инициализировать расширение для поиска по семантике: %s", e
        )


async def init_vector_extension(engine: AsyncEngine):
    try:
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
    except Exception as e:
        logger.exception(
            "Не удалось инициализировать расширение для поиска по семантике: %s", e
        )
