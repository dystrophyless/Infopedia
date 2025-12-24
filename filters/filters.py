import logging

from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message

from sqlalchemy.ext.asyncio import AsyncSession

from enums.roles import UserRole
from database.db import get_user_role
from services.signature import verify_payload

logger = logging.getLogger(__name__)


class LocaleFilter(BaseFilter):
    async def __call__(self, callback: CallbackQuery, locales: list):
        if not isinstance(callback, CallbackQuery):
            raise ValueError(
                f"LocaleFilter: expected `CallbackQuery`, got `{type(callback).__name__}`"
            )
        return callback.data in locales


class UserRoleFilter(BaseFilter):
    def __init__(self, *roles: str | UserRole):
        if not roles:
            raise ValueError("At least one role must be provided to UserRoleFilter.")

        self.roles = frozenset(
            UserRole(role) if isinstance(role, str) else role
            for role in roles
            if isinstance(role, (str, UserRole))
        )

        if not self.roles:
            raise ValueError("No valid roles provided to `UserRoleFilter`.")

    async def __call__(self, event: Message | CallbackQuery, session: AsyncSession) -> bool:
        user = event.from_user
        if not user:
            return False

        role = await get_user_role(session, user_id=user.id)
        if role is None:
            return False

        return role in self.roles


class ActionPayloadFilter(BaseFilter):
    def __init__(self, action: str):
        self.action = action

    async def __call__(self, message: Message):
        if not message.text or not message.text.startswith(self.action):
            return False

        payload = verify_payload(message.text)

        username: str = message.from_user.username if message.from_user.username else message.from_user.first_name

        await message.delete()

        if payload is None:
            logger.debug("Злоумышленник с `username`='%s' попытался сфальсифицировать payload.", username)
            return False

        if payload.get("action") != self.action:
            return False

        return {"payload": payload}