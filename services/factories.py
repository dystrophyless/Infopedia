from functools import lru_cache

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

from config_data.config import Config, load_config
from database.connection import get_sessionmaker_cached
from services.nlp import get_embedder, get_reranker
from services.definition_service import DefinitionService


@lru_cache(maxsize=1)
def get_config() -> Config:
    return load_config(".env")


@lru_cache(maxsize=1)
def get_db_sessionmaker():
    config = get_config()
    return get_sessionmaker_cached(
        db_name=config.db.name,
        host=config.db.host,
        port=config.db.port,
        user=config.db.user,
        password=config.db.password,
    )


def create_bot() -> Bot:
    config = get_config()

    return Bot(
        token=config.bot.token,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
            link_preview_is_disabled=True,
        ),
    )


def create_dispatcher() -> tuple[Dispatcher, Redis]:
    config = get_config()

    redis = Redis(
        host=config.redis.host,
        port=config.redis.port,
        db=config.redis.db,
        password=config.redis.password,
        username=config.redis.username,
    )
    storage = RedisStorage(redis=redis)
    dp = Dispatcher(storage=storage)

    return dp, redis


@lru_cache(maxsize=1)
def get_definition_service() -> DefinitionService:
    return DefinitionService(
        embedder=get_embedder(),
        reranker=get_reranker(),
    )