import logging
from urllib.parse import quote
from functools import lru_cache

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
        f"postgresql+psycopg://{quote(user, safe='')}@{host}:{port}/{db_name}",
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


@lru_cache(maxsize=1)
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


@lru_cache(maxsize=1)
def get_sessionmaker_cached(
    db_name: str,
    host: str,
    port: int,
    user: str,
    password: str,
    echo: bool = False,
    pool_size: int = 5,
    max_overflow: int = 10,
) -> async_sessionmaker[AsyncSession]:
    return get_sessionmaker(
        get_async_engine(
            db_name=db_name,
            host=host,
            port=port,
            user=user,
            password=password,
            echo=echo,
            pool_size=pool_size,
            max_overflow=max_overflow,
        )
    )


async def init_similarity_extension(engine: AsyncEngine):
    try:
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))
            await conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_terms_name_trgm ON terms USING gin (name gin_trgm_ops);",
                ),
            )

        logger.debug("Расширение для поиска по семантике успешно инициализировано")
    except Exception as e:
        logger.exception(
            "Не удалось инициализировать расширение для поиска по семантике: %s",
            e,
        )


async def init_vector_extension(engine: AsyncEngine):
    try:
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))

        logger.debug("Расширение для векторного поиска успешно инициализировано")
    except Exception as e:
        logger.exception(
            "Не удалось инициализировать расширение для векторного поиска: %s",
            e,
        )
