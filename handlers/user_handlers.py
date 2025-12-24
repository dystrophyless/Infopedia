import logging

from contextlib import suppress

from aiogram import Router, Bot, F
from aiogram.enums import BotCommandScopeType
from aiogram.types import Message, CallbackQuery, BotCommandScopeChat
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import default_state
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from sqlalchemy.ext.asyncio import AsyncSession

from keyboards.inline_keyboards import build_search_kb, build_suggestion_kb, build_considering_definition_kb, build_repeating_search_definition_kb
from keyboards.main_menu import build_menu_kb, build_main_menu_kb
from keyboards.menu_commands import get_main_menu_commands
from services.definition_service import DefinitionService
from services.term_service import TermService
from services.notification_service import NotificationService
from utils.callback_factories import TermCallback
from database.models import Term, Source, Definition
from database.db import get_user_role, add_search_feedback
from fsm.states import FSMSearch
from enums.roles import UserRole
from filters.filters import ActionPayloadFilter

logger = logging.getLogger(__name__)

router = Router()


@router.message(Command(commands=["start"]), StateFilter(default_state))
async def process_start_command(
    message: Message,
    i18n: dict,
    state: FSMContext,
    bot: Bot,
    session: AsyncSession
):
    await message.answer(
        text=i18n.get("/start"),
        reply_markup=build_menu_kb(i18n)
    )

    user_role: str = await state.get_value("user_role")

    if user_role is None:
        user_role: UserRole = await get_user_role(session, user_id=message.from_user.id)
    else:
        user_role: UserRole = UserRole(user_role)

    await bot.set_my_commands(
        commands=get_main_menu_commands(i18n=i18n, role=user_role),
        scope=BotCommandScopeChat(
            type=BotCommandScopeType.CHAT,
            chat_id=message.from_user.id
        )
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


@router.callback_query(F.data == "search")
async def process_search_button(
    callback: CallbackQuery,
    i18n: dict
):
    await callback.message.edit_text(
        text=i18n.get("choose_search_type"),
        reply_markup=build_search_kb(i18n)
    )
    await callback.answer()


@router.callback_query(F.data == "find_term_by_definition")
async def process_find_term_by_definition(
    callback: CallbackQuery,
    i18n: dict,
    state: FSMContext,
    bot: Bot
):
    msg_id = await state.get_value("consider_definition_msg_id")
    if msg_id:
        await bot.edit_message_reply_markup(
            chat_id=callback.from_user.id,
            message_id=msg_id,
            reply_markup=None
        )

    await state.update_data(consider_definition_msg_id=None)

    await callback.message.answer(
        text=i18n.get("await_definition_to_recognize"),
    )
    await callback.answer()

    await state.set_state(FSMSearch.await_definition_to_recognize)


@router.callback_query(F.data == "back_to_main_menu")
async def process_going_back_to_main_menu(
    callback: CallbackQuery,
    total_users_count: int,
    total_terms_count: int,
    i18n: dict,
    state: FSMContext
):
    user_role: str = await state.get_value("user_role")

    await callback.message.edit_text(
        text=i18n.get("main_menu").format(total_users_count, total_terms_count, i18n.get(user_role)),
        reply_markup=build_main_menu_kb(i18n)
    )

    await state.set_state()


@router.message(StateFilter(FSMSearch.await_definition_to_recognize), F.text.regexp(r"^\S+(?:\s+\S+)+$"))
async def process_appropriate_definition(
    message: Message,
    i18n: dict,
    bot: Bot,
    state: FSMContext,
    session: AsyncSession,
    definition_service: DefinitionService,
):
    msg = await message.answer(text=i18n.get("awaiting_response"))

    definition: Definition = await definition_service.find_best(session, query=message.text)

    if definition is None:
        msg = await bot.edit_message_text(
            text=i18n.get("definition_was_not_found"),
            reply_markup=build_repeating_search_definition_kb(i18n),
            chat_id=message.from_user.id,
            message_id=msg.message_id
        )

        await state.set_state()
    else:
        source: Source = definition.source
        term: Term = definition.source.term

        await bot.edit_message_text(
            text=i18n.get("definition_representation").format(term.name, definition.text, source.name, definition.topic, definition.page),
            chat_id=message.from_user.id,
            message_id=msg.message_id
        )

        msg = await message.answer(
            text=i18n.get("consider_definition"),
            reply_markup=build_considering_definition_kb(i18n)
        )

        await state.update_data(query=message.text, definition_id=definition.id)
        await state.set_state(FSMSearch.await_considering_definition)

    await state.update_data(consider_definition_msg_id=msg.message_id)


@router.message(StateFilter(FSMSearch.await_definition_to_recognize))
async def process_inappropriate_definition(
    message: Message,
    i18n: dict,
    state: FSMContext
):
    await message.answer(i18n.get("wrong_definition_length"))

    await state.set_state()


@router.callback_query(F.data == "definition_was_exact", StateFilter(FSMSearch.await_considering_definition))
async def process_definition_was_exact(
    callback: CallbackQuery,
    i18n: dict,
    state: FSMContext,
    session: AsyncSession,
):
    definition_id: int = await state.get_value("definition_id")
    query: str = await state.get_value("query")

    await callback.message.edit_text(
        text=i18n.get("exact_definition_feedback"),
        reply_markup=build_repeating_search_definition_kb(i18n)
    )

    await add_search_feedback(session, user_id=callback.from_user.id, definition_id=definition_id, query=query, correct=True)

    await state.update_data(definition_id=None, query=None)
    await state.set_state()


@router.callback_query(F.data == "definition_was_not_exact", StateFilter(FSMSearch.await_considering_definition))
async def process_definition_was_exact(
    callback: CallbackQuery,
    i18n: dict,
    state: FSMContext,
    session: AsyncSession,
):
    definition_id: int = await state.get_value("definition_id")
    query: str = await state.get_value("query")

    await callback.message.edit_text(
        text=i18n.get("not_exact_definition_feedback"),
        reply_markup=build_repeating_search_definition_kb(i18n)
    )

    await add_search_feedback(session, user_id=callback.from_user.id, definition_id=definition_id, query=query, correct=False)

    await state.update_data(definition_id=None, query=None)
    await state.set_state()


@router.message(StateFilter(FSMSearch.await_considering_definition))
async def process_failed_to_consider_definition(
    message: Message,
    i18n: dict,
    state: FSMContext,
    bot: Bot
):
    with suppress(TelegramBadRequest):
        msg_id = await state.get_value("consider_definition_msg_id")
        if msg_id:
            await bot.delete_message(chat_id=message.from_user.id, message_id=msg_id)

    msg = await message.answer(
        text=i18n.get("consider_definition"),
        reply_markup=build_considering_definition_kb(i18n)
    )

    await state.update_data(consider_definition_msg_id=msg.message_id)


@router.message(ActionPayloadFilter("get_term_info"))
async def process_getting_term_info(
    message: Message,
    i18n: dict,
    session: AsyncSession,
    payload: dict,
    term_service: TermService
):
    text, kb = await term_service.get_term(session, term_name=payload["term"], i18n=i18n)

    await message.answer(text=text, reply_markup=kb)


@router.callback_query(F.data == "noop")
async def process_answer_nothing(
    callback: CallbackQuery,
    i18n: dict
):
    await callback.answer(text=i18n.get("noop"))


@router.message(ActionPayloadFilter("suggest_new_term"))
async def process_definition_suggestion(
    message: Message,
    i18n: dict,
    payload: dict
):
    suggested_term: str = payload["term"]

    await message.answer(
        text=i18n.get("suggest_new_term").format(suggested_term),
        reply_markup=build_suggestion_kb(i18n, suggested_term)
    )

    username: str = message.from_user.username if message.from_user.username else message.from_user.first_name
    logger.debug(f"Пользователь {username} хочет предложить следующий термин с `name`=`{suggested_term}`")


@router.callback_query(F.data.startswith("suggestion_positive_reply"))
async def process_suggestion_positive_reply(
    callback: CallbackQuery,
    bot: Bot,
    group_id: str,
    i18n: dict
):
    suggested_term: str = callback.data.split(":")[1]

    await callback.message.edit_text(
        text=i18n.get("suggestion_positive_reply").format(suggested_term)
    )

    await NotificationService.send_new_suggestion_alert(bot, callback.from_user, chat_id=group_id, term=suggested_term)

    username: str = callback.from_user.username if callback.from_user.username else callback.from_user.first_name
    logger.debug("Пользователь с `username`='%s' предложил следующий термин: %s", username, suggested_term)


@router.callback_query(F.data == "suggestion_negative_reply")
async def process_suggestion_negative_reply(callback: CallbackQuery):
    await callback.message.delete()


@router.callback_query(TermCallback.filter())
async def process_definition_change(
    callback: CallbackQuery,
    callback_data: TermCallback,
    i18n: dict,
    session: AsyncSession,
    term_service: TermService
):
    text, kb = await term_service.get_definition(session, term_id=callback_data.term_id, source_id=callback_data.source_id, index=callback_data.index, i18n=i18n)

    await callback.message.edit_text(
        text=text,
        reply_markup=kb
    )
    await callback.answer()
