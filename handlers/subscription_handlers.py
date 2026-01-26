import logging
from contextlib import suppress

from aiogram import Router, Bot, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter

from keyboards.main_menu import build_buy_subscription_confirmation_kb, build_process_subscription_receipt_kb, build_back_kb
from fsm.states import FSMSubscription
from services.mention import get_user_link

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(F.data == "buy_subscription")
async def process_buy_subscription_button(
    callback: CallbackQuery,
    i18n: dict,
    state: FSMContext
):
    if await state.get_state() == FSMSubscription.await_receipt:
        await state.set_state()

    from_menu: bool = await state.get_value("from_menu")

    await callback.message.edit_text(
        text=i18n.get("buy_subscription_info"),
        reply_markup=build_buy_subscription_confirmation_kb(i18n, back_to_get_informed_about_roles=from_menu)
    )
    await callback.answer()


@router.callback_query(F.data == "confirm_buy_subscription")
async def process_confirm_buy_subscription_button(
    callback: CallbackQuery,
    i18n: dict,
    state: FSMContext,
):
    msg = await callback.message.edit_text(
        text=i18n.get("confirm_buy_subscription_info"),
        reply_markup=build_back_kb(i18n=i18n, callback_data="buy_subscription")
    )
    await callback.answer()

    await state.set_state(FSMSubscription.await_receipt)
    await state.update_data(confirm_buy_subscription_info_msg_id=msg.message_id)


@router.message(F.document.mime_type == "application/pdf", StateFilter(FSMSubscription.await_receipt))
async def process_appropriate_subscription_receipt(
    message: Message,
    group_id: str,
    i18n: dict,
    bot: Bot,
    state: FSMContext
):
    with suppress(TelegramBadRequest):
        msg_id = await state.get_value("confirm_buy_subscription_info_msg_id")
        if msg_id:
            await bot.edit_message_reply_markup(
                chat_id=message.from_user.id,
                message_id=msg_id,
                reply_markup=None
            )

    await message.answer(
        text=i18n.get("subscription_receipt_received")
    )


    await bot.send_document(
        chat_id=group_id,
        caption=f"📬 Пришел запрос о подтверждении подписки!\n\n"
             f"👤 От пользователя: {get_user_link(user_id=message.from_user.id, username=message.from_user.username, first_name=message.from_user.first_name)}\n\n"
             f"🧾 Проверьте квитанцию и подтвердите подписку.",
        document=message.document.file_id,
        reply_markup=build_process_subscription_receipt_kb(message.from_user.id)
    )

    await state.set_state()
    await state.update_data(confirm_buy_subscription_info_msg_id=None, ubscription_receipt_incorrect_format_msg_id=None)


@router.message(StateFilter(FSMSubscription.await_receipt))
async def process_inappropriate_subscription_receipt(
    message: Message,
    i18n: dict,
    bot: Bot,
    state: FSMContext
):
    with suppress(TelegramBadRequest):
        bot_msg_id = await state.get_value("subscription_receipt_incorrect_format_msg_id")
        user_msg_id = await state.get_value("incorrect_format_msg_id")
        if bot_msg_id and user_msg_id:
            await bot.delete_message(chat_id=message.from_user.id, message_id=user_msg_id)
            await bot.delete_message(chat_id=message.from_user.id, message_id=bot_msg_id)

    msg = await message.answer(
        text=i18n.get("subscription_receipt_incorrect_format")
    )

    await state.update_data(subscription_receipt_incorrect_format_msg_id=msg.message_id)
    await state.update_data(incorrect_format_msg_id=message.message_id)





