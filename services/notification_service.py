from html import escape
from aiogram import Bot
from aiogram.types import User

from keyboards.inline_keyboards import build_suggestion_decision_kb
from services.mention import get_user_link

class NotificationService:
    @classmethod
    async def send_new_suggestion_alert(
        cls,
        *,
        bot: Bot,
        user: User,
        chat_id: str,
        term: str
    ):
        text = (
            f"📄 Было предложено добавить новый термин: <b>{escape(term)}</b>\n\n"
            f"👤 От пользователя: {get_user_link(user_id=user.id, username=user.username, first_name=user.first_name)}"
        )

        await bot.send_message(
            text=text,
            chat_id=chat_id,
            reply_markup=build_suggestion_decision_kb(user.id)
        )