import logging

from aiogram import Bot
from aiogram.enums.chat_member_status import ChatMemberStatus

logger = logging.getLogger(__name__)


async def is_user_followed(bot: Bot, user_id: int, channel_id: str) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        return member.status in [
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.CREATOR,
        ]
    except Exception:
        logger.debug("Что-то пошло не так при проверке подписки")
        return False
