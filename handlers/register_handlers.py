import logging
from psycopg import AsyncConnection

from aiogram import Router, Bot, F
from aiogram.enums import BotCommandScopeType
from aiogram.types import Message, CallbackQuery, BotCommandScopeChat
from aiogram.filters import Command, StateFilter, MagicData
from aiogram.fsm.context import FSMContext

from fsm.states import FSMRegister
from enums.roles import UserRole
from services.membership import is_user_followed
from keyboards.inline_keyboards import build_channel_kb, build_language_kb, build_grade_kb
from keyboards.menu_commands import get_main_menu_commands
from database.db import add_user

logger = logging.getLogger(__name__)

router = Router()


@router.message(Command(commands=["start"]), MagicData(F.start_registration))
async def process_start_registration(
    message: Message,
    bot: Bot,
    state: FSMContext,
    channel_id: str,
    channel_link: str,
    i18n: dict,
):
    await message.answer(text=i18n.get("/start"))
    if await is_user_followed(bot, message.from_user.id, channel_id):
        await message.answer(
            text=i18n.get("choose_language"),
            reply_markup=build_language_kb()
        )
        await state.set_state(FSMRegister.choose_language)
    else:
        await message.answer(
            text=i18n.get("await_membership"),
            reply_markup=build_channel_kb(channel_link)
        )
        await state.set_state(FSMRegister.await_membership)
    logger.debug(f'Пользователь {message.from_user.username} начал проходить этап регистрации')


@router.callback_query(F.data == "check_membership", StateFilter(FSMRegister.await_membership))
async def process_channel_link_press(
    callback: CallbackQuery,
    bot: Bot,
    state: FSMContext,
    channel_id: str,
    i18n: dict
):
    if await is_user_followed(bot, callback.message.from_user.id, channel_id):
        await callback.answer()
        await callback.message.edit_text(text='✅ Вы прошли проверку на подписку!')

        await callback.message.answer(
            text=i18n.get("choose_language"),
            reply_markup=build_language_kb()
        )
        await state.set_state(FSMRegister.choose_language)
    else:
        await callback.answer(
            text=i18n.get("unsuccessful_membership"),
            show_alert=True
        )


@router.message(StateFilter(FSMRegister.await_membership))
async def process_failed_to_channel_link_press(
    message: Message,
    i18n: dict
):
    await message.answer(text=i18n.get("failed_to_await_membership"))


@router.callback_query(F.data.in_(["kz", "ru"]), StateFilter(FSMRegister.choose_language))
async def process_choosing_language(
    callback: CallbackQuery,
    bot: Bot,
    state: FSMContext,
    i18n: dict
):
    await callback.message.edit_text(
        text=i18n.get("choose_grade").format(i18n.get(callback.data)),
        reply_markup=build_grade_kb()
    )
    await state.set_state(FSMRegister.choose_grade)
    await state.update_data(user_language=callback.data)

    user_data = await state.get_data()
    user_role: UserRole = user_data.get("user_role")

    await bot.set_my_commands(
        commands=get_main_menu_commands(i18n=i18n, role=user_role),
        scope=BotCommandScopeChat(
            type=BotCommandScopeType.CHAT,
            chat_id=callback.from_user.id
        )
    )


@router.message(StateFilter(FSMRegister.choose_language))
async def process_failed_to_choose_language(
    message: Message,
    i18n: dict
):
    await message.answer(text=i18n.get("failed_to_choose_language"))


@router.callback_query(F.data.in_(["grade_10", "grade_11", "grade_undefined"]), StateFilter(FSMRegister.choose_grade))
async def process_choosing_grade(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: dict,
    conn: AsyncConnection
):
    user_data = await state.get_data()

    user_id = callback.from_user.id
    username = f'{callback.from_user.username}' if callback.from_user.username else "undefined"
    user_language = user_data.get("user_language")
    user_grade = callback.data[6:]
    user_role = user_data.get("user_role")

    await add_user(
        conn,
        user_id=user_id,
        username=username,
        language=user_language,
        grade=user_grade,
        role=user_role
    )

    await callback.message.edit_text(
        text=i18n.get("finish_registration").format(i18n.get(callback.data))
    )

    await state.update_data(user_role=None, user_language=None)
    await state.set_state()


@router.message(StateFilter(FSMRegister.choose_grade))
async def process_failed_to_choose_grade(message: Message):
    await message.answer(
        text="Пожалуйста, выберите класс, в котором вы учитесь на данный момент.\n"
        "Для этого, нажмите соответствующую кнопку выше."
    )
