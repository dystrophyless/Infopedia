import logging

from html import escape

from aiogram import Router, Bot, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import default_state

from sqlalchemy.ext.asyncio import AsyncSession

from keyboards.inline_keyboards import build_search_kb, build_suggestion_kb, build_suggestion_decision_kb, build_sources_kb
from keyboards.main_menu import build_main_menu_kb
from services.signature import verify_payload
from services.terms import get_term_info
from utils.callback_factories import TermCallback
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

    username: str = message.from_user.username if message.from_user.username else message.from_user.first_name
    logger.debug(f"Пользователь {username} начал чат с ботом")


@router.message(Command(commands=["help"]), StateFilter(default_state))
async def process_help_command(
    message: Message,
    i18n: dict
):
    await message.answer(text=i18n.get("/help"))

    username: str = message.from_user.username if message.from_user.username else message.from_user.first_name
    logger.debug(f"Пользователь {username} прописал команду /help")


@router.message(F.text.startswith("get_term_info"))
async def process_getting_term_info(
    message: Message,
    i18n: dict,
    session: AsyncSession
):
    data = verify_payload(message.text)

    await message.delete()

    username: str = message.from_user.username if message.from_user.username else message.from_user.first_name

    if data is None:
        logger.debug("Злоумышленник с `username`='%s' попытался сфальсифицировать payload.", username)
        return

    term: Term = await get_term_by_name(session, name=data["term"])

    if term is None:
        logger.debug("Не удалось найти термин `name=%s` в базе данных", term)
        return

    if data["action"] == "get_term_info":
        text, kb = await get_term_info(term=term, i18n=i18n)

        if text is None:
            logger.debug("Не удалось найти термин `name=%s` в базе данных", data["term"])
            return

        await message.answer(text=text, reply_markup=kb)


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
    data = verify_payload(message.text)

    await message.delete()

    username: str = message.from_user.username if message.from_user.username else message.from_user.first_name

    if data is None:
        logger.debug("Злоумышленник с `username`='%s' попытался сфальсифицировать payload.", username)
        return

    if data["action"] == "suggest_new_term":
        suggested_term: str = data["term"]

        await message.answer(
            text=i18n.get("suggest_new_term").format(suggested_term),
            reply_markup=build_suggestion_kb(i18n, suggested_term)
        )
        logger.debug(f"Пользователь {username} предложил следующий термин с `name`=`{suggested_term}`")


@router.callback_query(F.data.startswith("suggestion_positive_reply"))
async def process_suggestion_positive_reply(
    callback: CallbackQuery,
    bot: Bot,
    group_id: str,
    i18n: dict
):
    suggested_term: str = callback.data.split(":")[1]
    username: str = callback.from_user.username if callback.from_user.username else callback.from_user.first_name
    exact_username: str = callback.from_user.username

    await callback.message.edit_text(
        text=i18n.get("suggestion_positive_reply").format(suggested_term)
    )

    if exact_username:
        link = f"https://t.me/{username}"
        username = f"@{username}"
    else:
        link = f"tg://user?id={callback.from_user.id}"

    await bot.send_message(
        chat_id=group_id,
        text=f"📄 Было предложено добавить новый термин: <b>{suggested_term}</b>\n\n"
             f"👤 От пользователя: <a href=\"{link}\">{escape(username)}</a>",
        reply_markup=build_suggestion_decision_kb(callback.from_user.id)
    )
    logger.debug("Пользователь с `username`='%s' предложил следующий термин: %s", username, suggested_term)


@router.callback_query(F.data == "suggestion_negative_reply")
async def process_suggestion_negative_reply(callback: CallbackQuery):
    await callback.message.delete()


@router.callback_query(TermCallback.filter())
async def process_definition_change(
    callback: CallbackQuery,
    callback_data: TermCallback,
    i18n: dict,
    session: AsyncSession
):
    term: Term = await get_term_by_id(session, id=callback_data.term_id)
    source: Source = await get_source_by_id(session, id=callback_data.source_id)
    index = callback_data.index

    text, kb = await get_term_info(term=term, source=source, index=index, i18n=i18n)

    if text is None:
        logger.debug("Не удалось перейти к источнику/дефиниции у термина с `name`='%s'", term.name)
        return

    await callback.message.edit_text(
        text=text,
        reply_markup=kb
    )
    await callback.answer()
