import logging
import html

from aiogram import Router, Bot, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup
from aiogram.filters import Command, StateFilter, MagicData
from aiogram.fsm.state import default_state

from sqlalchemy.ext.asyncio import AsyncSession

from keyboards.main_menu import build_profile_menu_kb, build_main_menu_kb
from database.db import get_user_language, get_user_grade, get_user_role


logger = logging.getLogger(__name__)

router = Router()


@router.message(F.text == "👤 Профиль")
async def process_profile_menu_button(
    message: Message,
    i18n: dict,
    session: AsyncSession
):
    await message.delete()

    username = message.from_user.username if message.from_user.username else message.from_user.first_name
    user_language: str = await get_user_language(session, user_id=message.from_user.id)
    user_role: str = await get_user_role(session, user_id=message.from_user.id)

    await message.answer(
        text=i18n.get("profile_menu").format(username, i18n.get(user_language), i18n.get(user_role)),
        reply_markup=build_profile_menu_kb(i18n)
    )


@router.message(F.text == "🏠 Главная")
async def process_main_menu_button(
    message: Message,
    i18n: dict,
    total_users_count: int,
    total_terms_count: int,
    session: AsyncSession
):
    await message.delete()

    user_role: str = await get_user_role(session, user_id=message.from_user.id)

    await message.answer(
        text=i18n.get("main_menu").format(total_users_count, total_terms_count, i18n.get(user_role)),
        reply_markup=build_main_menu_kb(i18n)
    )