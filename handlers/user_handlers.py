import logging
import html

from aiogram import Router, Bot, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import default_state

from sqlalchemy.ext.asyncio import AsyncSession

from keyboards.inline_keyboards import build_search_kb, build_suggestion_kb, build_suggestion_decision_kb, build_sources_kb
from keyboards.main_menu import build_main_menu_kb
from services.signature import verify_payload
from utils.callback_factories import SourceCallback, TermCallback
from database.models import Term, Source, Definition
from database.db import get_user_role, get_term_by_name, get_term_by_id, get_source_by_id

logger = logging.getLogger(__name__)

router = Router()


@router.message(Command(commands=["start"]), StateFilter(default_state))
async def process_start_command(
    message: Message,
    i18n: dict,
    total_users_count: int,
    total_terms_count: int,
    session: AsyncSession
):
    user_role: str = await get_user_role(session, user_id=message.from_user.id)

    await message.answer(
        text=i18n.get("main_menu").format(total_users_count, total_terms_count, i18n.get(user_role)),
        reply_markup = build_main_menu_kb(i18n)
    )

    username = message.from_user.username if message.from_user.username else message.from_user.first_name
    logger.debug(f"Пользователь {username} начал чат с ботом")


@router.message(Command(commands=["help"]), StateFilter(default_state))
async def process_help_command(
    message: Message,
    i18n: dict
):
    await message.answer(text=i18n.get("/help"))

    username = message.from_user.username if message.from_user.username else message.from_user.first_name
    logger.debug(f"Пользователь {username} прописал команду /help")


@router.message(F.text.startswith("get_term_info"))
async def process_getting_term_info(
    message: Message,
    i18n: dict,
    session: AsyncSession
):
    data = verify_payload(message.text)

    await message.delete()

    username = message.from_user.username if message.from_user.username else message.from_user.first_name

    if data is None:
        logger.debug("Злоумышленник с `username`='%s' попытался сфальсифицировать payload.", username)
        return

    if data["action"] == "get_term_info":
        term_name = data["term"]

        term: Term = await get_term_by_name(session, name=term_name)

        if term is None:
            logger.debug("Не удалось найти термин `name=%s` в базе данных", term)
            return

        sources: list[Source] = term.sources

        first_source: Source = sources[0]

        first_source_definition: Definition = first_source.definitions[0]

        definition: str = html.escape(first_source_definition.text)
        topic: str = html.escape(first_source_definition.topic)
        page: int = first_source_definition.page

        await message.answer(
            text=i18n.get("get_term_info").format(term.name, definition, topic, page),
            reply_markup=build_sources_kb(term=term, current_source_name=first_source.name),
        )


@router.callback_query(F.data == "noop")
async def process_answer_nothing(
    callback: CallbackQuery,
    i18n: dict
):
    await callback.answer(text=i18n.get("noop"))


@router.message(F.text.startswith("suggest_new_term"))
async def process_definition_suggestion(
    message: Message,
    i18n: dict
):
    suggested_term: str = message.text.split(":")[1]
    await message.delete()
    await message.answer(
        text=i18n.get("suggest_new_term").format(suggested_term),
        reply_markup=build_suggestion_kb(i18n, suggested_term)
    )
    username = message.from_user.username if message.from_user.username else message.from_user.first_name
    logger.debug(f"Пользователь {username} предложил следующий термин с `name`=`{suggested_term}`")


@router.callback_query(F.data.startswith("suggestion_positive_reply"))
async def process_suggestion_positive_reply(
    callback: CallbackQuery,
    bot: Bot,
    group_id: str,
    i18n: dict
):
    suggested_term = callback.data.split(":")[1]
    username = callback.from_user.username if callback.from_user.username else callback.from_user.first_name

    await callback.message.edit_text(
        text=i18n.get("suggestion_positive_reply")
    )
    await bot.send_message(
        chat_id=group_id,
        text=f"📄 Было предложено добавить новый термин: <b>{suggested_term}</b>\n\n"
             f"👤 От пользователя: <a href=\"tg://user?id={callback.from_user.id}\">{username}</a>",
        reply_markup=build_suggestion_decision_kb(callback.from_user.id)
    )
    logger.debug("Пользователь с `username`='%s' предложил следующий термин: %s", username, suggested_term)


@router.callback_query(F.data == "suggestion_negative_reply")
async def process_suggestion_negative_reply(callback: CallbackQuery):
    await callback.message.delete()


@router.callback_query(SourceCallback.filter())
async def process_source_change(
    callback: CallbackQuery,
    callback_data: SourceCallback,
    i18n: dict,
    session: AsyncSession
):
    term: Term = await get_term_by_id(session, id=callback_data.term_id)
    source: Source = await get_source_by_id(session, id=callback_data.source_id)
    definitions: list[Definition] = source.definitions

    if not definitions:
        logging.debug(f"У источника {source} не найдены дефиниции для термина {term}.")
        return

    first_definition: Definition = definitions[0]

    definition: str = html.escape(first_definition.text)
    topic: str = html.escape(first_definition.topic)
    page: int = first_definition.page

    await callback.message.edit_text(
        text=i18n.get("get_term_info").format(term.name, definition, topic, page),
        reply_markup=build_sources_kb(term=term, current_source_name=source.name)
    )
    await callback.answer()


@router.callback_query(TermCallback.filter())
async def process_definition_change(
    callback: CallbackQuery,
    callback_data: TermCallback,
    i18n: dict,
    session: AsyncSession
):
    term: Term = await get_term_by_id(session, id=callback_data.term_id)
    source: Source = await get_source_by_id(session, id=callback_data.source_id)
    definitions: list[Definition] = source.definitions
    index = callback_data.index

    if not definitions:
        logging.debug(f"У источника {source} не найдены дефиниции для термина {term}.")
        return

    indexed_definition = definitions[index]

    definition = html.escape(indexed_definition.text)
    topic = html.escape(indexed_definition.topic)
    page = indexed_definition.page

    await callback.message.edit_text(
        text=i18n.get("get_term_info").format(term.name, definition, topic, page),
        reply_markup=build_sources_kb(term=term, current_source_name=source.name, current_index=index)
    )
    await callback.answer()
