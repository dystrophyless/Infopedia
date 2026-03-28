import asyncio
import io
import logging
import logging.config
import os
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

from config_data.config import Config, load_config
from database.connection import (
    get_async_engine,
    get_sessionmaker,
    init_similarity_extension,
)
from database.create_tables import create_tables
from database.db import get_total_terms, get_total_users
from database.loader import load_terms_from_json, load_chapters_and_topic_codes, load_books_topics_and_mappings
from handlers import (
    admin_handlers,
    inline_handlers,
    language_handlers,
    menu_handlers,
    register_handlers,
    subscription_handlers,
    user_handlers,
)
from i18n.translator import get_translations
from logs.logging_settings import logging_config
from middlewares.database import DatabaseMiddleware
from middlewares.feature_usage import FeatureUsageMiddleware
from middlewares.i18n import TranslatorMiddleware
from middlewares.language_settings import LanguageSettingsMiddleware
from middlewares.membership import MembershipMiddleware
from middlewares.registration import RegistrationMiddleware
from middlewares.shadow_ban import ShadowBanMiddleware
from middlewares.statistics import ActivityCounterMiddleware
from middlewares.throttler import ThrottlingMiddleware
from services.definition_service import DefinitionService
from services.nlp import embedder, reranker
from services.term_service import TermService

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, write_through=True)

logger = logging.getLogger(__name__)


async def main() -> None:
    logging.config.dictConfig(logging_config)

    logger.debug("Процесс запуск бота был начат")

    config: Config = load_config(".env")

    storage = RedisStorage(
        redis=Redis(
            host=config.redis.host,
            port=config.redis.port,
            db=config.redis.db,
            password=config.redis.password,
            username=config.redis.username,
        ),
    )

    bot = Bot(
        token=config.bot.token,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
            link_preview_is_disabled=True,
        ),
    )
    dp = Dispatcher(storage=storage)

    engine = get_async_engine(
        db_name=config.db.name,
        host=config.db.host,
        port=config.db.port,
        user=config.db.user,
        password=config.db.password,
    )

    await create_tables(engine)

    sessionmaker = get_sessionmaker(engine)

    async with sessionmaker() as session:
        await load_chapters_and_topic_codes(session, "database/mappingStructure.json")
        logger.debug("Главы и коды тем успешно загружены в БД")

        await load_books_topics_and_mappings(session, "database/newStructure.json")
        logger.debug("Книги, темы и их связи успешно загружены в БД")

        await load_terms_from_json(session, embedder, "database/terms.json")
        logger.debug("Термины успешно загружены в БД")

    await init_similarity_extension(engine)

    definition_service: DefinitionService = DefinitionService(embedder, reranker)
    term_service: TermService = TermService()

    total_users_count: int = await get_total_users(sessionmaker)
    total_terms_count: int = await get_total_terms(sessionmaker)

    translations = get_translations()
    locales = list(translations.keys())

    dp.include_router(register_handlers.router)
    dp.include_router(language_handlers.router)
    dp.include_router(inline_handlers.router)
    dp.include_router(admin_handlers.router)
    dp.include_router(user_handlers.router)
    dp.include_router(menu_handlers.router)
    dp.include_router(subscription_handlers.router)

    dp.update.outer_middleware(ThrottlingMiddleware())
    dp.update.outer_middleware(DatabaseMiddleware())
    dp.update.outer_middleware(RegistrationMiddleware())
    dp.update.outer_middleware(MembershipMiddleware())
    dp.update.outer_middleware(ShadowBanMiddleware())
    dp.update.outer_middleware(ActivityCounterMiddleware())
    dp.update.outer_middleware(LanguageSettingsMiddleware())
    dp.update.outer_middleware(TranslatorMiddleware())
    dp.message.middleware(FeatureUsageMiddleware())
    dp.callback_query.middleware(FeatureUsageMiddleware())

    dp["bot"] = bot
    dp["channel_id"] = config.bot.channel_id
    dp["channel_link"] = config.bot.channel_link
    dp["admin_ids"] = config.bot.admin_ids
    dp["group_id"] = config.bot.group_id
    dp["sessionmaker"] = sessionmaker
    dp["definition_service"] = definition_service
    dp["term_service"] = term_service
    dp["total_users_count"] = total_users_count
    dp["total_terms_count"] = total_terms_count
    dp["translations"] = translations
    dp["locales"] = locales

    try:
        logger.debug("Сбрасываем апдейты которые были получены когда бот был выключен")
        await bot.delete_webhook(drop_pending_updates=True)

        logger.debug("Начинаем получать апдейты от Telegram")
        await dp.start_polling(bot)
    except Exception as e:
        logger.exception(e)
    finally:
        await engine.dispose()
        logger.debug("Соединение с PostgreSQL было закрыто")


if __name__ == "__main__":
    if sys.platform.startswith("win") or os.name == "nt":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main())
