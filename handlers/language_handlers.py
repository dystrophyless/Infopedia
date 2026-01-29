import logging
from contextlib import suppress

from aiogram import Bot, F, Router
from aiogram.enums import BotCommandScopeType
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, BotCommandScopeChat

from filters.filters import LocaleFilter
from keyboards.inline_keyboards import build_language_settings_kb
from keyboards.main_menu import build_main_menu_kb
from keyboards.menu_commands import get_main_menu_commands
from fsm.states import FSMLanguage
from database.models import Users
from enums.roles import UserRole

logger = logging.getLogger(__name__)

router = Router()


@router.message(StateFilter(FSMLanguage.choose_language))
async def process_any_message_when_language(
    message: Message, bot: Bot, i18n: dict, locales: list[str], state: FSMContext
):
    user_id = message.from_user.id

    user_language = await state.get_value("user_language")

    with suppress(TelegramBadRequest):
        msg_id = await state.get_value("language_settings_msg_id")
        if msg_id:
            await bot.delete_message(chat_id=user_id, message_id=msg_id)

    msg = await message.answer(
        text=i18n.get("/language"),
        reply_markup=build_language_settings_kb(
            i18n=i18n, locales=locales, checked=user_language
        ),
    )

    await state.update_data(language_settings_msg_id=msg.message_id)


@router.callback_query(F.data == "change_language")
async def process_language_command(
    callback: CallbackQuery,
    i18n: dict,
    locales: list[str],
    state: FSMContext,
    db_user: Users,
):
    await state.set_state(FSMLanguage.choose_language)
    user_language: str = db_user.language

    msg = await callback.message.edit_text(
        text=i18n.get("/language"),
        reply_markup=build_language_settings_kb(
            i18n=i18n, locales=locales, checked=user_language
        ),
    )

    await state.update_data(
        language_settings_msg_id=msg.message_id, user_language=user_language
    )


@router.callback_query(
    F.data == "save_language_button_data", FSMLanguage.choose_language
)
async def process_save_click(
    callback: CallbackQuery, bot: Bot, i18n: dict, state: FSMContext, db_user: Users
):
    data = await state.get_data()
    db_user.language = data.get("user_language")
    await callback.message.edit_text(
        text=i18n.get("language_saved").format(
            user_language=i18n.get(data.get("user_language"))
        )
    )

    user_role: UserRole = db_user.role

    await bot.set_my_commands(
        commands=get_main_menu_commands(i18n=i18n, role=user_role),
        scope=BotCommandScopeChat(
            type=BotCommandScopeType.CHAT, chat_id=callback.from_user.id
        ),
    )

    await state.update_data(language_settings_msg_id=None, user_language=None)
    await state.set_state()


@router.callback_query(
    F.data == "cancel_language_button_data", FSMLanguage.choose_language
)
async def process_cancel_click(
    callback: CallbackQuery,
    i18n: dict,
    total_users_count: int,
    total_terms_count: int,
    state: FSMContext,
    db_user: Users,
):
    user_language: str = db_user.language
    user_role: UserRole = db_user.role

    await callback.answer(
        text=i18n.get("language_cancelled").format(
            user_language=i18n.get(user_language)
        )
    )

    await callback.message.edit_text(
        text=i18n.get("main_menu").format(
            total_users=total_users_count,
            total_terms=total_terms_count,
            user_role=i18n.get(user_role),
        ),
        reply_markup=build_main_menu_kb(i18n),
    )

    await state.update_data(
        language_settings_msg_id=None, user_language=None, user_role=user_role
    )
    await state.set_state()


@router.callback_query(LocaleFilter(), FSMLanguage.choose_language)
async def process_language_click(
    callback: CallbackQuery, i18n: dict, locales: list[str]
):
    try:
        await callback.message.edit_text(
            text=i18n.get("/language"),
            reply_markup=build_language_settings_kb(
                i18n=i18n, locales=locales, checked=callback.data
            ),
        )
    except TelegramBadRequest:
        await callback.answer()
