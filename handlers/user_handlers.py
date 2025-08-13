import logging

from aiogram import Router, Bot, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import default_state

from keyboards.inline_keyboards import build_search_kb, build_suggestion_kb, build_suggestion_decision_kb, build_sources_kb
from services.signature import verify_payload
from utils.callback_factories import SourceCallback, TermCallback

logger = logging.getLogger(__name__)

router = Router()


@router.message(Command(commands=["start"]), StateFilter(default_state))
async def process_start_command(
    message: Message,
    i18n: dict
):
    await message.answer(text=i18n.get("/start"))
    username = f"{message.from_user.username}" if message.from_user.username else "Неизвестный"
    logger.debug(f"Пользователь {username} начал чат с ботом")


@router.message(Command(commands=["help"]), StateFilter(default_state))
async def process_help_command(
    message: Message,
    i18n: dict
):
    await message.answer(text=i18n.get("/help"))
    username = f"{message.from_user.username}" if message.from_user.username else "Неизвестный"
    logger.debug(f"Пользователь {username} прописал команду /help")


@router.message(Command(commands=["find"]))
async def process_find_command(
    message: Message,
    i18n: dict
):
    await message.answer(
        text=i18n.get("/find"),
        reply_markup=build_search_kb()
    )
    username = f"{message.from_user.username}" if message.from_user.username else "Неизвестный"
    logger.debug(f"Пользователь {username} прописал команду /find")


@router.message(F.text.startswith("suggest_new_definition"))
async def process_definition_suggestion(
    message: Message,
    i18n: dict
):
    suggested_definition: str = message.text.split(":")[1]
    await message.delete()
    await message.answer(
        text=i18n.get("suggest_new_definition").format(suggested_definition),
        reply_markup=build_suggestion_kb(suggested_definition)
    )
    username = f"{message.from_user.username}" if message.from_user.username else "Неизвестный"
    logger.debug(f"Пользователь {username} прописал команду /help")


@router.message(F.text.startswith("get_term_info"))
async def process_getting_term_info(
    message: Message,
    i18n: dict,
    terms: dict,
    term_names_to_ids: dict[str, int],
    source_names_to_ids: dict[str, int]
):
    data = verify_payload(message.text)

    await message.delete()

    if data is None:
        return

    if data["action"] == "get_term_info":
        term = data["term"]
        if term not in terms:
            logger.debug(f"Термин не найден: {term}")
            return

        sources = terms[term]

        first_source_name, first_source_entries = next(iter(sources.items()))

        first_source_entry = first_source_entries[0]

        definition = first_source_entry["definition"]
        topic = first_source_entry["topic"]
        page = first_source_entry["page"]

        await message.answer(
            text=i18n.get("get_term_info").format(term, definition, topic, page),
            reply_markup=build_sources_kb(term, terms, term_names_to_ids, source_names_to_ids, first_source_name, 0)
        )


@router.callback_query(F.data == "noop")
async def process_answer_nothing(
    callback: CallbackQuery,
    i18n: dict
):
    await callback.answer(text=i18n.get("noop"))


@router.callback_query(F.data.startswith("suggestion_positive_reply"))
async def process_suggestion_positive_reply(
    callback: CallbackQuery,
    bot: Bot,
    group_id: str,
    i18n: dict
):
    suggested_definition = callback.data.split(":")[1]
    username = f"{callback.from_user.username}" if callback.from_user.username else "Неизвестный"

    await callback.message.edit_text(
        text=i18n.get("suggestion_positive_reply")
    )
    await bot.send_message(
        chat_id=group_id,
        text=f'📄 Было предложено добавить новый термин: <b>{suggested_definition}</b>\n\n'
             f'👤 От пользователя: <a href="tg://user?id={callback.from_user.id}">{username}</a>',
        reply_markup=build_suggestion_decision_kb(callback.from_user.id)
    )
    logger.debug(f"Пользователь {username} предложил следующий термин: {suggested_definition}")


@router.callback_query(F.data == "suggestion_negative_reply")
async def process_suggestion_negative_reply(callback: CallbackQuery):
    await callback.message.delete()


@router.callback_query(SourceCallback.filter())
async def process_source_change(
    callback: CallbackQuery,
    callback_data: SourceCallback,
    i18n: dict,
    terms: dict,
    term_names_to_ids: dict[str, int],
    source_names_to_ids: dict[str, int],
    term_ids: dict[int, str],
    source_ids: dict[int, str]
):
    term = term_ids[callback_data.term]
    source = source_ids[callback_data.source]

    sources = terms[term]

    entries = sources.get(source)

    if not entries:
        logging.debug(f"Источник {source} не найден для термина {term}.")
        return

    first_entry = entries[0]

    definition = first_entry["definition"]
    topic = first_entry["topic"]
    page = first_entry["page"]

    await callback.message.edit_text(
        text=i18n.get("get_term_info").format(term, definition, topic, page),
        reply_markup=build_sources_kb(term, terms, term_names_to_ids, source_names_to_ids, source, 0)
    )
    await callback.answer()


@router.callback_query(TermCallback.filter())
async def process_definition_change(
    callback: CallbackQuery,
    callback_data: TermCallback,
    i18n: dict,
    terms: dict,
    term_ids: dict[int, str],
    source_ids: dict[int, str],
    term_names_to_ids: dict[str, int],
    source_names_to_ids: dict[str, int]
):
    term = term_ids[callback_data.term]
    source = source_ids[callback_data.source]
    index = callback_data.index

    sources = terms[term]

    entries = sources.get(source)

    if not entries:
        logging.debug(f"Источник {source} не найден для термина {term}.")
        return

    first_entry = entries[index]

    definition = first_entry["definition"]
    topic = first_entry["topic"]
    page = first_entry["page"]

    await callback.message.edit_text(
        text=i18n.get("get_term_info").format(term, definition, topic, page),
        reply_markup=build_sources_kb(term, terms, term_names_to_ids, source_names_to_ids, source, index)
    )
    await callback.answer()
