import logging
import asyncio
from contextlib import suppress

from aiogram import Router, Bot, F
from aiogram.enums import BotCommandScopeType
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message, CallbackQuery, BotCommandScopeChat
from aiogram.filters import Command, StateFilter, MagicData, state
from aiogram.fsm.context import FSMContext

from sqlalchemy.ext.asyncio import AsyncSession

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
    if await is_user_followed(bot, message.from_user.id, channel_id):
        msg = await message.answer(
            text=i18n.get("choose_language"),
            reply_markup=build_language_kb()
        )
        await state.set_state(FSMRegister.choose_language)
        await state.update_data(registration_msg_id=msg.message_id)
    else:
        msg = await message.answer(
            text=i18n.get("await_membership"),
            reply_markup=build_channel_kb(channel_link)
        )
        await state.set_state(FSMRegister.await_membership)
        await state.update_data(await_membership_msg_id=msg.message_id)

    username = message.from_user.username if message.from_user.username else message.from_user.first_name
    logger.debug("Пользователь с `username`='%s' начал проходить этап регистрации", username)


@router.callback_query(F.data == "check_membership", StateFilter(FSMRegister.await_membership))
async def process_channel_link_press(
    callback: CallbackQuery,
    bot: Bot,
    state: FSMContext,
    channel_id: str,
    i18n: dict
):
    username = callback.from_user.username if callback.from_user.username else callback.from_user.first_name
    logger.debug("Пользователь с `username`='%s' начал проходить этап подписки в регистрации", username)

    if await is_user_followed(bot, callback.from_user.id, channel_id):
        logger.debug("Пользователь с `username`='%s' был подписан на наш канал, ожидаем выбор языка", username)
        await callback.answer()
        await callback.message.edit_text(text=i18n.get("successful_membership"))

        msg_id = await callback.message.answer(
            text=i18n.get("choose_language"),
            reply_markup=build_language_kb()
        )
        await state.set_state(FSMRegister.choose_language)
        await state.update_data(registration_msg_id=msg_id.message_id)
    else:
        logger.debug("Пользователь с `username`='%s' не был подписан на наш канал, ожидем подписку", username)
        await callback.answer(
            text=i18n.get("unsuccessful_membership"),
            show_alert=True
        )




@router.message(StateFilter(FSMRegister.await_membership))
async def process_failed_to_channel_link_press(
    message: Message,
    bot: Bot,
    i18n: dict,
    channel_link: str,
    state: FSMContext
):
    user_id = message.from_user.id

    with suppress(TelegramBadRequest):
        msg_id = await state.get_value("await_membership_msg_id")
        if msg_id:
            await bot.delete_message(chat_id=user_id, message_id=msg_id)

    msg = await message.answer(
        text=i18n.get("await_membership"),
        reply_markup=build_channel_kb(channel_link)
    )

    await state.update_data(await_membership_msg_id=msg.message_id)


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

    user_role: UserRole = await state.get_value("user_role")

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
    bot: Bot,
    i18n: dict,
    state: FSMContext
):
    user_id = message.from_user.id

    with suppress(TelegramBadRequest):
        msg_id = await state.get_value("registration_msg_id")
        if msg_id:
            await bot.delete_message(chat_id=user_id, message_id=msg_id)

    msg_id = await message.answer(
        text=i18n.get("choose_language"),
        reply_markup=build_language_kb()
    )

    await state.update_data(registration_msg_id=msg_id.message_id)



@router.callback_query(F.data.in_(["grade_10", "grade_11", "grade_undefined"]), StateFilter(FSMRegister.choose_grade))
async def process_choosing_grade(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: dict,
    session: AsyncSession
):
    user_id = callback.from_user.id
    username = callback.from_user.username if callback.from_user.username else callback.from_user.first_name
    user_language = await state.get_value("user_language")
    user_grade = callback.data[6:]
    user_role = await state.get_value("user_role")

    await add_user(
        session,
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

    await asyncio.sleep(3)

    await callback.message.delete()

    await callback.message.answer(text=i18n.get("thanks_for_registration"))




@router.message(StateFilter(FSMRegister.choose_grade))
async def process_failed_to_choose_grade(
    message: Message,
    bot: Bot,
    i18n: dict,
    state: FSMContext
):
    user_id = message.from_user.id

    with suppress(TelegramBadRequest):
        msg_id = await state.get_value("registration_msg_id")
        if msg_id:
            await bot.delete_message(chat_id=user_id, message_id=msg_id)

    user_language = await state.get_value("user_language")

    msg_id = await message.answer(
        text=i18n.get("choose_grade").format(i18n.get(user_language)),
        reply_markup=build_grade_kb()
    )

    await state.update_data(registration_msg_id=msg_id.message_id)


