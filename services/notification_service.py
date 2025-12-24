from html import escape
from aiogram import Bot
from aiogram.types import User
from keyboards.inline_keyboards import build_suggestion_decision_kb


class NotificationService:
    @staticmethod
    def _get_user_mention(user: User) -> str:
        if user.username:
            link = f"https://t.me/{user.username}"
            display_name = f"@{user.username}"
        else:
            link = f"tg://user?id={user.id}"
            display_name = user.first_name

        return f'<a href="{link}">{escape(display_name)}</a>'

    @classmethod
    async def send_new_suggestion_alert(
        cls,
        bot: Bot,
        user: User,
        *,
        chat_id: str,
        term: str
    ):
        mention = cls._get_user_mention(user)

        text = (
            f"📄 Было предложено добавить новый термин: <b>{escape(term)}</b>\n\n"
            f"👤 От пользователя: {mention}"
        )

        await bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=build_suggestion_decision_kb(user.id)
        )