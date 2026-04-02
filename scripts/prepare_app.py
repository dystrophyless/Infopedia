import asyncio
import logging
import logging.config

from config_data.config import Config, load_config
from database.create_tables import create_tables
from database.connection import get_async_engine, get_sessionmaker, init_similarity_extension
from database.loader import load_terms_from_json, load_books_topics_and_mappings, load_chapters_and_topic_codes
from logs.logging_settings import logging_config
from services.nlp import get_embedder


logger = logging.getLogger(__name__)


async def main() -> None:
    logging.config.dictConfig(logging_config)

    config: Config = load_config(".env")

    engine = get_async_engine(
        db_name=config.db.name,
        host=config.db.host,
        port=config.db.port,
        user=config.db.user,
        password=config.db.password,
    )
    sessionmaker = get_sessionmaker(engine)

    try:
        embedder = get_embedder()

        await create_tables(engine)

        async with sessionmaker() as session:
            await load_chapters_and_topic_codes(session, "database/mappingStructure.json")
            logger.debug("Главы и коды тем успешно загружены в БД")

            await load_books_topics_and_mappings(session, "database/newStructure.json")
            logger.debug("Книги, темы и их связи успешно загружены в БД")

            await load_terms_from_json(session, embedder,"database/terms.json")
            logger.debug("Термины успешно загружены")

        await init_similarity_extension(engine)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())