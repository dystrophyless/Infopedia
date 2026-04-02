import asyncio

from aiogram import Bot, Dispatcher

from celery_app.app import app
from keyboards.inline_keyboards import (
    build_considering_definition_kb,
    build_repeating_search_definition_kb,
)
from services.factories import get_definition_service, get_db_sessionmaker, create_bot, create_dispatcher
from fsm.states import FSMSearch


async def _send_successful_result_message(
    *,
    bot: Bot,
    dp: Dispatcher,
    query: str,
    info: dict,
    chat_id: int,
    message_id: int,
    i18n: dict,
) -> None:
    text = i18n.get("definition_representation").format(
        term=info["term"],
        book=info["book"],
        text=info["text"],
        topic=info["topic"],
        page=info["page"],
    )

    state = dp.fsm.get_context(
        bot=bot,
        chat_id=chat_id,
        user_id=chat_id,
    )

    await state.set_state(FSMSearch.await_considering_definition)
    await state.update_data(definition_id=info["definition_id"])

    await bot.edit_message_text(
        chat_id=chat_id,
        message_id=message_id,
        text=text,
    )

    msg = await bot.send_message(
        chat_id=chat_id,
        text=i18n.get("consider_definition"),
        reply_markup=build_considering_definition_kb(i18n),
    )

    await state.update_data(
        query=query,
        definition_id=info["definition_id"],
        consider_definition_msg_id=msg.message_id,
    )
    await state.set_state(FSMSearch.await_considering_definition)


async def _send_unsuccessful_result_message(
    *,
    bot: Bot,
    dp: Dispatcher,
    chat_id: int,
    message_id: int,
    i18n: dict,
) -> None:
    state = dp.fsm.get_context(
        bot=bot,
        chat_id=chat_id,
        user_id=chat_id,
    )

    await bot.edit_message_text(
        chat_id=chat_id,
        message_id=message_id,
        text=i18n.get("definition_was_not_found"),
        reply_markup=build_repeating_search_definition_kb(i18n),
    )

    await state.update_data(
        consider_definition_msg_id=message_id,
        from_menu=None,
    )
    await state.set_state(None)


async def _run_search(query: str) -> dict | None:
    definition_service = get_definition_service()
    sessionmaker = get_db_sessionmaker()

    async with sessionmaker() as session:
        return await definition_service.get_search_result(
            session=session,
            query=query,
        )


async def _process_query_async(
    *,
    chat_id: int,
    message_id: int,
    i18n: dict,
    query: str,
) -> None:
    bot = create_bot()
    dp, redis = create_dispatcher()

    try:
        result = await _run_search(query)

        if result is None:
            await _send_unsuccessful_result_message(
                bot=bot,
                dp=dp,
                chat_id=chat_id,
                message_id=message_id,
                i18n=i18n,
            )
        else:
            await _send_successful_result_message(
                bot=bot,
                dp=dp,
                query=query,
                info=result,
                chat_id=chat_id,
                message_id=message_id,
                i18n=i18n,
            )
    finally:
        await bot.session.close()
        await redis.aclose()


@app.task(
    name="search_task.process_query",
    ignore_result=True,
)
def process_query(
    chat_id: int,
    message_id: int,
    i18n: dict,
    query: str,
) -> None:
    asyncio.run(
        _process_query_async(
            chat_id=chat_id,
            message_id=message_id,
            i18n=i18n,
            query=query,
        )
    )