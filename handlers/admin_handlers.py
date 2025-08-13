import logging

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import BaseFilter

logger = logging.getLogger(__name__)

router = Router()

class isAdmin(BaseFilter):
    async def __call__(self, message: Message, admin_ids: list[int]) -> bool:
        return message.from_user.id in admin_ids

router.message.filter(isAdmin())


