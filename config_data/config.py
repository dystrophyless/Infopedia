from dataclasses import dataclass
from typing import Optional

from environs import Env


@dataclass
class BotSettings:
    token: str
    group_id: str
    channel_id: str
    channel_link: str
    admin_ids: list[int]
    signature: str


@dataclass
class DatabaseSettings:
    name: str
    host: str
    port: int
    user: str
    password: str


@dataclass
class RedisSettings:
    host: str
    port: int
    db: int
    password: str
    username: str


@dataclass
class Config:
    bot: BotSettings
    db: DatabaseSettings
    redis: RedisSettings


def load_config(path: Optional[str] = None) -> Config:
    env: Env = Env()
    env.read_env(path, override=True)

    bot = BotSettings(
        token=env("BOT_TOKEN"),
        group_id=env("GROUP_ID"),
        channel_id=env("CHANNEL_ID"),
        channel_link=env("CHANNEL_LINK"),
        admin_ids=list(map(int, env.list("ADMIN_ID"))),
        signature=env("SIGNATURE"),
    )

    db = DatabaseSettings(
        name=env("POSTGRES_DB"),
        host=env("POSTGRES_HOST"),
        port=env.int("POSTGRES_PORT"),
        user=env("POSTGRES_USER"),
        password=env("POSTGRES_PASSWORD"),
    )

    redis = RedisSettings(
        host=env("REDIS_HOST"),
        port=env.int("REDIS_PORT"),
        db=env.int("REDIS_DATABASE"),
        password=env("REDIS_PASSWORD", default=""),
        username=env("REDIS_USERNAME", default=""),
    )

    return Config(bot=bot, db=db, redis=redis)
