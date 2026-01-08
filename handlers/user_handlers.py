import logging
import asyncio

from contextlib import suppress

from aiogram import Router, Bot, F
from aiogram.enums import BotCommandScopeType
from aiogram.types import Message, CallbackQuery, BotCommandScopeChat
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import default_state
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from sqlalchemy.ext.asyncio import AsyncSession

from exceptions import TermNotFoundByNameError, TermNotFoundByIdError, TermPresentationError
from keyboards.inline_keyboards import build_search_kb, build_suggestion_kb, build_considering_definition_kb, build_repeating_search_definition_kb
from keyboards.main_menu import build_menu_kb, build_main_menu_kb
from keyboards.menu_commands import get_main_menu_commands
from services.definition_service import DefinitionService
from services.term_service import TermService
from services.notification_service import NotificationService
from services.feedback_service import FeedbackService
from services.user_service import UserService
from ui.progressive_messages import ProgressiveMessage
from utils.callback_factories import TermCallback
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

    user_role: UserRole = await UserService.get_role(
        session,
        state=state,
        user_id=message.from_user.id
    )

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

    await state.update_data(
        consider_definition_msg_id=None
    )

    await callback.message.answer(
        text=i18n.get("await_definition_to_recognize")
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
        text=i18n.get("main_menu").format(
            total_users=total_users_count,
            total_terms=total_terms_count,
            user_role=i18n.get(user_role)
        ),
        reply_markup=build_main_menu_kb(i18n)
    )

    await state.set_state()


@router.message(StateFilter(FSMSearch.await_definition_to_recognize), F.text.regexp(r"^\S+(?:\s+\S+)+$"))
async def process_appropriate_definition(
    message: Message,
    i18n: dict,
    state: FSMContext,
    session: AsyncSession,
    definition_service: DefinitionService,
):
    status_msg = await message.answer(i18n.get("awaiting_response"))

    progress = ProgressiveMessage(message=status_msg)
    progress.set_stage_mapping({
        "embedding": i18n.get("step_understanding"),
        "searching": i18n.get("step_searching"),
        "reranking": i18n.get("step_clarifying"),
        "deciding": i18n.get("step_preparing"),
    })

    await progress.start()

    async def on_stage(stage: str):
        await progress.update_stage(stage)

    # --- создаём задачу поиска с callback ---
    search_task = asyncio.create_task(
        definition_service.get_search_result(
            session,
            query=message.text,
            on_stage=on_stage
        )
    )

    definition, info = await search_task
    await progress.stop()  # ✅ останавливаем прогресс после получения результата

    if definition is None:
        await status_msg.edit_text(
            text=i18n.get("definition_was_not_found"),
            reply_markup=build_repeating_search_definition_kb(i18n),
        )

        await state.update_data(
            consider_definition_msg_id=status_msg.message_id
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
    state: FSMContext
):
    await message.answer(
        text=i18n.get("wrong_definition_length")
    )

    await state.set_state()


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


@router.message(ActionPayloadFilter("get_term_info"))
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


@router.callback_query(F.data == "noop")
async def process_answer_nothing(
    callback: CallbackQuery,
    i18n: dict
):
    await callback.answer(
        text=i18n.get("noop")
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
