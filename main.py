import asyncio
import logging
import logging.config
import psycopg_pool
import os
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage

from redis.asyncio import Redis

from logs.logging_settings import logging_config
from config_data.config import Config, load_config
from services.data import load_terms, load_indexed_terms, generate_id_maps
from handlers import register_handlers, language_handlers, user_handlers, admin_handlers, inline_handlers
from i18n.translator import get_translations
from database.connection import get_pg_pool

from middlewares.throttler import ThrottlingMiddleware
from middlewares.database import DatabaseMiddleware
from middlewares.registration import RegistrationMiddleware
from middlewares.membership import MembershipMiddleware
from middlewares.language_settings import LanguageSettingsMiddleware
from middlewares.i18n import TranslatorMiddleware
from middlewares.shadow_ban import ShadowBanMiddleware
from middlewares.statistics import ActivityCounterMiddleware


logger = logging.getLogger(__name__)


async def main() -> None:
    logging.config.dictConfig(logging_config)

    logger.debug('Процесс запуск бота был начат')

    config: Config = load_config('.env')

    terms = load_terms()
    indexed_terms = load_indexed_terms()
    term_ids, term_names_to_ids, source_ids, source_names_to_ids = generate_id_maps(terms)

    storage = RedisStorage(
        redis=Redis(
            host=config.redis.host,
            port=config.redis.port,
            db=config.redis.db,
            password=config.redis.password,
            username=config.redis.username,
        )
    )

    bot = Bot(
        token=config.bot.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=storage)

    db_pool: psycopg_pool.AsyncConnectionPool = await get_pg_pool(
        db_name=config.db.name,
        host=config.db.host,
        port=config.db.port,
        user=config.db.user,
        password=config.db.password,
    )

    translations = get_translations()
    locales = list(translations.keys())

    dp.include_router(register_handlers.router)
    dp.include_router(language_handlers.router)
    dp.include_router(inline_handlers.router)
    dp.include_router(admin_handlers.router)
    dp.include_router(user_handlers.router)

    dp.update.outer_middleware(ThrottlingMiddleware())
    dp.update.outer_middleware(DatabaseMiddleware())
    dp.update.outer_middleware(RegistrationMiddleware())
    dp.update.middleware(MembershipMiddleware())
    dp.update.middleware(ShadowBanMiddleware())
    dp.update.middleware(ActivityCounterMiddleware())
    dp.update.middleware(LanguageSettingsMiddleware())
    dp.update.middleware(TranslatorMiddleware())


    dp['bot'] = bot
    dp['channel_id'] = config.bot.channel_id
    dp['channel_link'] = config.bot.channel_link
    dp['admin_ids'] = config.bot.admin_ids
    dp['group_id'] = config.bot.group_id
    dp['terms'] = terms
    dp['indexed_terms'] = indexed_terms
    dp['term_ids'] = term_ids
    dp['term_names_to_ids'] = term_names_to_ids
    dp['source_ids'] = source_ids
    dp['source_names_to_ids'] = source_names_to_ids
    dp['db_pool'] = db_pool
    dp['translations'] = translations
    dp['locales'] = locales

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except Exception as e:
        logger.exception(e)
    finally:
        await db_pool.close()
        logger.debug("Соединение с PostgreSQL было закрыто")

if __name__ == '__main__':
    if sys.platform.startswith("win") or os.name == "nt":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main())
