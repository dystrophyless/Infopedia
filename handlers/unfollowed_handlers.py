import logging

from aiogram import Router, Bot, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import default_state
from aiogram.fsm.context import FSMContext

from fsm.states import FSMMembership
from keyboards.inline_keyboards import build_channel_kb
from services.membership import is_user_followed


logger = logging.getLogger(__name__)

router = Router()


@router.message(StateFilter(FSMMembership))
async def process_any_message(message: Message, i18n: dict, channel_link: str, state: FSMContext):
    await message.answer(
        text=i18n.get("channel_membership"),
        reply_markup = build_channel_kb(channel_link)
    )


@router.callback_query(F.data == 'check_channel_subscription', StateFilter(FSMMembership.await_membership))
async def process_channel_link_press(callback: CallbackQuery, bot: Bot, channel_id: str, i18n: dict, state: FSMContext):
    if await is_user_followed(bot, callback.message.from_user.id, channel_id):
        await callback.answer()
        await callback.message.edit_text(text='✅ Вы прошли проверку на подписку!')
        await state.set_state()
    else:
        await callback.answer(
            text=i18n.get("unsuccessful_subscription"),
            show_alert=True
        )
