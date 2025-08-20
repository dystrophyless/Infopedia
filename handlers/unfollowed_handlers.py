import logging

from aiogram import Router, Bot, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.filters import MagicData, StateFilter

from keyboards.inline_keyboards import build_channel_kb
from services.membership import is_user_followed
from fsm.states import FSMMembership


logger = logging.getLogger(__name__)

router = Router()


@router.message(MagicData(F.await_membership))
async def process_any_message(
    message: Message,
    i18n: dict,
    channel_link: str,
    state: FSMContext
):
    await message.answer(
        text=i18n.get("channel_membership"),
        reply_markup = build_channel_kb(channel_link)
    )

    await state.set_state(FSMMembership.await_membership)

    username = f"{message.from_user.username}" if message.from_user.username else "Неизвестный"
    logger.debug("Пользователь с username=`%s` который был зарегистрирован отписался от Infopedia, поэтому требуем обратную подписки", username)


@router.callback_query(F.data == 'check_membership', StateFilter(FSMMembership.await_membership))
async def process_channel_link_press(
    callback: CallbackQuery,
    bot: Bot,
    state: FSMContext,
    channel_id: str,
    i18n: dict,
):
    if await is_user_followed(bot, callback.from_user.id, channel_id):
        await callback.answer()
        await callback.message.edit_text(text=i18n.get("successful_membership"))

        await state.set_state()
    else:
        await callback.answer(
            text=i18n.get("unsuccessful_subscription"),
            show_alert=True
        )
