import logging
import asyncio

from contextlib import suppress

from aiogram import Router, Bot, F, flags
from aiogram.enums import BotCommandScopeType
from aiogram.types import Message, CallbackQuery, BotCommandScopeChat
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import default_state
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from sqlalchemy.ext.asyncio import AsyncSession

from exceptions import TermNotFoundByNameError, TermNotFoundByIdError, TermPresentationError
from keyboards.inline_keyboards import build_suggestion_kb, build_considering_definition_kb, build_repeating_search_definition_kb
from keyboards.main_menu import build_menu_kb, build_back_kb, build_buy_subscription_kb
from keyboards.menu_commands import get_main_menu_commands
from services.definition_service import DefinitionService
from services.term_service import TermService
from services.notification_service import NotificationService
from services.feedback_service import FeedbackService
from ui.progressive_messages import ProgressiveMessage
from utils.callback_factories import TermCallback
from fsm.states import FSMSearch
from enums.roles import UserRole
from enums.features import Feature
from filters.filters import ActionPayloadFilter, FeatureAccessFilter, UserRoleFilter
from database.models import Users

logger = logging.getLogger(__name__)

router = Router()


@router.message(Command(commands=["start"]), StateFilter(default_state))
async def process_start_command(
    message: Message,
    i18n: dict,
    bot: Bot,
    db_user: Users
):
    await message.answer(
        text=i18n.get("/start"),
        reply_markup=build_menu_kb(i18n)
    )

    user_role: UserRole = db_user.role

    await bot.set_my_commands(
        commands=get_main_menu_commands(
            i18n=i18n,
            role=user_role
        ),
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
    await message.answer(
        text=i18n.get("/help")
    )

    username: str = message.from_user.username if message.from_user.username else message.from_user.first_name
    logger.debug(f"Пользователь {username} прописал команду /help")


@router.callback_query(F.data == "find_term_by_definition", UserRoleFilter(UserRole.CLIENT, UserRole.ADMIN))
@router.callback_query(F.data == "find_term_by_definition", FeatureAccessFilter(Feature.DEFINITION_SEARCH))
async def process_find_term_by_definition(
    callback: CallbackQuery,
    i18n: dict,
    state: FSMContext,
    bot: Bot
):

    with suppress(TelegramBadRequest):
        msg_id = await state.get_value("consider_definition_msg_id")
        if msg_id:
            await bot.edit_message_reply_markup(
                chat_id=callback.from_user.id,
                message_id=msg_id,
                reply_markup=None
            )

    await state.update_data(
        consider_definition_msg_id=None
    )

    from_menu = await state.get_value("from_menu")

    if from_menu:
        await callback.message.delete()

    reply_markup = build_back_kb(i18n=i18n, callback_data="search") if from_menu else None

    msg = await callback.message.answer(
        text=i18n.get("await_definition_to_recognize"),
        reply_markup=reply_markup
    )
    await callback.answer()

    await state.set_state(FSMSearch.await_definition_to_recognize)
    await state.update_data(await_definition_msg_id=msg.message_id)


@router.callback_query(F.data == "find_term_by_definition")
async def process_no_access_to_get_term_by_definition(
    callback: CallbackQuery,
    i18n: dict,
    state: FSMContext,
    db_user: Users
):
    await state.update_data(from_menu=None)
    await callback.message.answer(
        text=i18n.get(Feature.DEFINITION_SEARCH.forbidden).format(usage_limit=Feature.DEFINITION_SEARCH.limit),
        reply_markup=build_buy_subscription_kb(i18n, user_role=db_user.role)
    )
    await callback.answer()



@router.message(StateFilter(FSMSearch.await_definition_to_recognize), F.text.regexp(r"^\S+(?:\s+\S+)+$"))
@flags.log_feature(feature=Feature.DEFINITION_SEARCH)
async def process_appropriate_definition(
    message: Message,
    i18n: dict,
    bot: Bot,
    state: FSMContext,
    session: AsyncSession,
    definition_service: DefinitionService,
):
    with suppress(TelegramBadRequest):
        msg_id = await state.get_value("await_definition_msg_id")
        if msg_id:
            await bot.edit_message_reply_markup(
                chat_id=message.from_user.id,
                message_id=msg_id,
                reply_markup=None
            )

    status_msg = await message.answer(i18n.get("awaiting_response"))

    progress = ProgressiveMessage(message=status_msg, update_interval=0.8, default_min_stage_time=0.0)
    progress.set_stage_mapping({
        "embedding": (i18n.get("step_understanding"), 1.8),
        "searching": (i18n.get("step_searching"), 3.6),
        "reranking": (i18n.get("step_clarifying"), 1.8),
        "deciding": (i18n.get("step_preparing"), 1.8),
    })
    await progress.start()

    async def on_stage(stage: str):
        await progress.update_stage(stage)

    definition, info = await definition_service.get_search_result(
        session,
        query=message.text,
        on_stage=on_stage
    )

    await progress.stop()

    if definition is None:
        await status_msg.edit_text(
            text=i18n.get("definition_was_not_found"),
            reply_markup=build_repeating_search_definition_kb(i18n),
        )

        await state.update_data(
            consider_definition_msg_id=status_msg.message_id,
            from_menu=None
        )
        await state.set_state()

        return

    await status_msg.edit_text(
        text=i18n.get("definition_representation").format(**info)
    )

    msg = await message.answer(
        text=i18n.get("consider_definition"),
        reply_markup=build_considering_definition_kb(i18n)
    )

    await state.update_data(
        query=message.text,
        definition_id=definition.id,
        consider_definition_msg_id=msg.message_id
    )
    await state.set_state(FSMSearch.await_considering_definition)


@router.message(StateFilter(FSMSearch.await_definition_to_recognize))
async def process_inappropriate_definition(
    message: Message,
    i18n: dict,
    bot: Bot,
    state: FSMContext
):
    with suppress(TelegramBadRequest):
        msg_id = await state.get_value("await_definition_msg_id")
        if msg_id:
            await bot.edit_message_reply_markup(
                chat_id=message.from_user.id,
                message_id=msg_id,
                reply_markup=None
            )

    msg = await message.answer(
        text=i18n.get("wrong_definition_length"),
        reply_markup=build_repeating_search_definition_kb(i18n)
    )

    await state.set_state()
    await state.update_data(consider_definition_msg_id=msg.message_id, from_menu=None)


@router.callback_query(F.data.in_(["definition_was_exact", "definition_was_not_exact"]), StateFilter(FSMSearch.await_considering_definition))
async def process_definition_was_exact(
    callback: CallbackQuery,
    i18n: dict,
    state: FSMContext,
    session: AsyncSession,
):
    correct = callback.data == "definition_was_exact"
    text_key = "exact_definition_feedback" if correct else "not_exact_definition_feedback"

    await callback.message.edit_text(
        text=i18n.get(text_key),
        reply_markup=build_repeating_search_definition_kb(i18n)
    )

    await callback.answer()

    await FeedbackService.add_feedback(
        session,
        state=state,
        user_id=callback.from_user.id,
        correct=correct
    )

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
            await bot.delete_message(
                chat_id=message.from_user.id,
                message_id=msg_id
            )

    msg = await message.answer(
        text=i18n.get("consider_definition"),
        reply_markup=build_considering_definition_kb(i18n)
    )

    await state.update_data(
        consider_definition_msg_id=msg.message_id
    )


@router.message(UserRoleFilter(UserRole.CLIENT, UserRole.ADMIN), ActionPayloadFilter("get_term_info"))
@router.message(FeatureAccessFilter(Feature.TERM_SEARCH), ActionPayloadFilter("get_term_info"))
@flags.log_feature(feature=Feature.TERM_SEARCH)
async def process_getting_term_info(
    message: Message,
    i18n: dict,
    session: AsyncSession,
    payload: dict,
    term_service: TermService
):
    try:
        text, kb = await term_service.get_term(session, term_name=payload["term"], i18n=i18n)
        await message.answer(
            text=text,
            reply_markup=kb
        )
    except TermNotFoundByNameError:
        await message.answer(
            text=i18n.get("term_was_not_found")
        )
    except TermPresentationError:
        await message.answer(
            text=i18n.get("term_presentation_error")
        )


@router.message(ActionPayloadFilter("get_term_info"))
async def process_no_access_to_get_term_info(
    message: Message,
    i18n: dict,
    state: FSMContext,
    db_user: Users
):
    await state.update_data(from_menu=None)
    await message.answer(
        text=i18n.get(Feature.TERM_SEARCH.forbidden).format(usage_limit=Feature.TERM_SEARCH.limit),
        reply_markup=build_buy_subscription_kb(i18n, user_role=db_user.role)
    )


@router.callback_query(F.data == "noop")
async def process_answer_nothing(
    callback: CallbackQuery,
    i18n: dict
):
    await callback.answer(
        text=i18n.get("noop_button")
    )


@router.message(ActionPayloadFilter("suggest_new_term"))
async def process_definition_suggestion(
    message: Message,
    i18n: dict,
    payload: dict
):
    suggested_term: str = payload["term"]

    await message.answer(
        text=i18n.get("suggest_new_term").format(
            term=suggested_term
        ),
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
        text=i18n.get("suggestion_positive_reply").format(
            term=suggested_term
        )
    )

    await NotificationService.send_new_suggestion_alert(
        bot=bot,
        user=callback.from_user,
        chat_id=group_id,
        term=suggested_term
    )

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
    try:
        text, kb = await term_service.get_definition(
            session,
            term_id=callback_data.term_id,
            source_id=callback_data.source_id,
            index=callback_data.index,
            i18n=i18n
        )

        await callback.message.edit_text(
            text=text,
            reply_markup=kb
        )
    except TermNotFoundByIdError:
        await callback.message.edit_text(
            text=i18n.get("term_was_not_found")
        )
    except TermPresentationError:
        await callback.message.edit_text(
            text=i18n.get("term_presentation_error")
        )
    finally:
        await callback.answer()



