import logging
from contextlib import suppress
from psycopg import AsyncConnection

from aiogram import Bot, F, Router
from aiogram.enums import BotCommandScopeType
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, BotCommandScopeChat

from filters.filters import LocaleFilter
from keyboards.inline_keyboards import build_language_settings_kb
from keyboards.menu_commands import get_main_menu_commands
from fsm.states import FSMLanguage
from database.db import get_user_language, get_user_role, update_user_language


logger = logging.getLogger(__name__)

router = Router()


@router.message(StateFilter(FSMLanguage.choose_language))
async def process_any_message_when_language(
    message: Message,
    bot: Bot,
    i18n: dict,
    locales: list[str],
    state: FSMContext
):
    user_id = message.from_user.id
    data = await state.get_data()
    user_language = data.get("user_language")

    with suppress(TelegramBadRequest):
        msg_id = data.get("language_settings_msg_id")
        if msg_id:
            await bot.delete_message(chat_id=user_id, message_id=msg_id)

    msg = await message.answer(
        text=i18n.get("/language"),
        reply_markup=build_language_settings_kb(i18n=i18n, locales=locales, checked=user_language)
    )

    await state.update_data(language_settings_msg_id=msg.message_id)


@router.message(Command(commands=["language"]))
async def process_language_command(
    message: Message,
    i18n: dict,
    locales: list[str],
    state: FSMContext,
    conn: AsyncConnection,
):
    await state.set_state(FSMLanguage.choose_language)
    user_language = await get_user_language(conn, user_id=message.from_user.id)

    msg = await message.answer(
        text=i18n.get("/language"),
        reply_markup=build_language_settings_kb(i18n=i18n, locales=locales, checked=user_language)
    )

    await state.update_data(language_settings_msg_id=msg.message_id, user_language=user_language)


@router.callback_query(F.data == "save_language_button_data")
async def process_save_click(
    callback: CallbackQuery,
    bot: Bot,
    i18n: dict,
    state: FSMContext,
    conn: AsyncConnection
):
    data = await state.get_data()
    await update_user_language(conn, language=data.get("user_language"), user_id=callback.from_user.id)
    await callback.message.edit_text(text=i18n.get("language_saved").format(i18n.get(data.get("user_language"))))

    user_role = await get_user_role(conn, user_id=callback.from_user.id)

    await bot.set_my_commands(
        commands=get_main_menu_commands(i18n=i18n, role=user_role),
        scope=BotCommandScopeChat(
            type=BotCommandScopeType.CHAT,
            chat_id=callback.from_user.id
        )
    )

    await state.update_data(language_settings_msg_id=None, user_language=None)
    await state.set_state()


@router.callback_query(F.data == "cancel_language_button_data")
async def process_cancel_click(
    callback: CallbackQuery,
    i18n: dict,
    state: FSMContext,
    conn: AsyncConnection
):
    user_language = await get_user_language(conn, user_id=callback.from_user.id)
    await callback.message.edit_text(text=i18n.get("language_cancelled").format(i18n.get(user_language)))
    await state.update_data(language_settings_msg_id=None, user_language=None)
    await state.set_state()


@router.callback_query(LocaleFilter())
async def process_language_click(
    callback: CallbackQuery,
    i18n: dict,
    locales: list[str]
):
    try:
        await callback.message.edit_text(
            text=i18n.get("/language"),
            reply_markup=build_language_settings_kb(i18n=i18n, locales=locales, checked=callback.data)
        )
    except TelegramBadRequest:
        await callback.answer()


