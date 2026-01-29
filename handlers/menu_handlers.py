import logging

from aiogram import Router, F, flags
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.state import default_state
from aiogram.fsm.context import FSMContext


from sqlalchemy.ext.asyncio import AsyncSession

from services.terms import get_term_info
from keyboards.main_menu import (
    build_profile_menu_kb,
    build_main_menu_kb,
    build_buy_subscription_kb,
)
from keyboards.inline_keyboards import build_search_kb
from database.db import get_user_language, get_user_role, get_random_terms
from database.models import Term, Users
from enums.roles import UserRole
from enums.features import Feature
from filters.filters import MenuFilter, FeatureAccessFilter, UserRoleFilter
from fsm.states import FSMLanguage


logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(MenuFilter("back_to_profile_menu"))
@router.message(MenuFilter("👤 Профиль"), StateFilter(default_state))
async def process_profile_menu_button(
    event: Message | CallbackQuery,
    i18n: dict,
    state: FSMContext,
    session: AsyncSession,
):
    username: str = (
        event.from_user.username
        if event.from_user.username
        else event.from_user.first_name
    )
    user_language: str = await get_user_language(session, user_id=event.from_user.id)
    user_role: str = await get_user_role(session, user_id=event.from_user.id)

    is_callback: bool = isinstance(event, CallbackQuery)
    is_coming_from_language: bool = (
        await state.get_state() == FSMLanguage.choose_language
    )
    message: Message = event.message if is_callback else event

    text = i18n.get("profile_menu").format(
        username=username,
        user_language=i18n.get(user_language),
        user_role=i18n.get(user_role),
    )

    if is_callback:
        if is_coming_from_language:
            await event.answer(
                text=i18n.get("language_cancelled").format(
                    user_language=i18n.get(user_language)
                )
            )

            await state.update_data(
                language_settings_msg_id=None, user_language=None, user_role=None
            )
            await state.set_state()
        await message.edit_text(text=text, reply_markup=build_profile_menu_kb(i18n))
    else:
        await message.answer(text=text, reply_markup=build_profile_menu_kb(i18n))

    await state.update_data(from_menu=True)


@router.callback_query(MenuFilter("back_to_main_menu"))
@router.message(MenuFilter("🏠 Главная"), StateFilter(default_state))
async def process_main_menu_button(
    event: Message | CallbackQuery,
    i18n: dict,
    total_users_count: int,
    total_terms_count: int,
    session: AsyncSession,
    state: FSMContext,
):
    user_role: str = await get_user_role(session, user_id=event.from_user.id)

    is_callback = isinstance(event, CallbackQuery)
    message: Message = event.message if is_callback else event

    text = i18n.get("main_menu").format(
        total_users=total_users_count,
        total_terms=total_terms_count,
        user_role=i18n.get(user_role),
    )

    if is_callback:
        await message.edit_text(text=text, reply_markup=build_main_menu_kb(i18n))
    else:
        await message.answer(text=text, reply_markup=build_main_menu_kb(i18n))

    await state.update_data(from_menu=True)


@router.callback_query(F.data == "search")
async def process_search_button(callback: CallbackQuery, i18n: dict, state: FSMContext):
    from_menu = await state.get_value("from_menu")

    await callback.message.edit_text(
        text=i18n.get("choose_search_type"),
        reply_markup=build_search_kb(i18n, back_to_main_menu=from_menu),
    )
    await callback.answer()

    await state.set_state()


@router.callback_query(
    F.data == "get_random_term", UserRoleFilter(UserRole.CLIENT, UserRole.ADMIN)
)
@router.callback_query(
    F.data == "get_random_term", FeatureAccessFilter(Feature.RANDOM_TERM)
)
@flags.log_feature(feature=Feature.RANDOM_TERM)
async def process_get_random_term_button(
    callback: CallbackQuery, i18n: dict, session: AsyncSession
):
    random_term: Term = (await get_random_terms(session, quantity=1))[0]

    text, kb = await get_term_info(term=random_term, i18n=i18n)

    await callback.message.answer(text=text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "get_random_term")
async def process_no_access_to_get_random_term(
    callback: CallbackQuery, i18n: dict, state: FSMContext, db_user: Users
):
    await state.update_data(from_menu=None)
    await callback.message.answer(
        text=i18n.get(Feature.RANDOM_TERM.forbidden).format(
            usage_limit=Feature.RANDOM_TERM.limit
        ),
        reply_markup=build_buy_subscription_kb(i18n, user_role=db_user.role),
    )
    await callback.answer()


@router.callback_query(F.data == "get_informed_about_roles")
async def process_get_informed_about_roles_button(
    callback: CallbackQuery,
    i18n: dict,
    state: FSMContext,
    session: AsyncSession,
):
    user_role: UserRole = await get_user_role(session, user_id=callback.from_user.id)

    from_menu = await state.get_value("from_menu")

    await callback.message.edit_text(
        text=i18n.get("roles_info").format(user_role=i18n.get(user_role)),
        reply_markup=build_buy_subscription_kb(
            i18n, user_role=user_role, back_to_profile=from_menu
        ),
    )
    await callback.answer()
