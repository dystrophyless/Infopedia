import logging

from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from enums.roles import UserRole
from enums.features import Feature
from database.db import get_user_role
from services.feature_usage import is_user_allowed_to_use_feature
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

        role: UserRole = await get_user_role(session, user_id=user.id)

        if role is None:
            return False

        return role in self.roles


class ActionPayloadFilter(BaseFilter):
    def __init__(self, action: str, usage_limit: int = 1):
        self.action = action
        self.usage_limit = usage_limit

    async def __call__(self, message: Message):
        if not message.text or not message.text.startswith(self.action):
            return False

        payload = verify_payload(message.text, self.usage_limit)

        username: str = message.from_user.username if message.from_user.username else message.from_user.first_name

        if payload is None:
            logger.debug("Злоумышленник с `username`='%s' попытался сфальсифицировать payload.", username)
            return False

        if payload.get("action") != self.action:
            return False

        await message.delete()
        return {"payload": payload}


class MenuFilter(BaseFilter):
    def __init__(self, filter_text: str | None = None):
        self.filter_text = filter_text

    async def __call__(self, event: Message | CallbackQuery):
        if isinstance(event, CallbackQuery):
            if event.data == self.filter_text:
                return await event.answer()

        if isinstance(event, Message):
            if event.text == self.filter_text:
                return await event.delete()

        return False


class FeatureAccessFilter(BaseFilter):
    def __init__(self, feature: Feature):
        self.feature = feature

    async def __call__(self, event: Message | CallbackQuery, session: AsyncSession):
        user_id: int = event.from_user.id

        is_allowed, usage_count = await is_user_allowed_to_use_feature(
            session=session,
            user_id=user_id,
            feature=self.feature,
        )

        if is_allowed:
            logger.debug("Пользователю с `user_id`='%d' разрешено использовать фичу с `feature_name`='%s' (%d/%d попыток)", user_id,
                     self.feature.name, usage_count, self.feature.limit)
            return True

        logger.warning("Пользователю с `user_id`='%d' запрещено использовать фичу с `feature_name`='%s' из-за превышения лимита использования", user_id,
                       self.feature.name)

        return False