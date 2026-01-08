from sqlalchemy.ext.asyncio import AsyncSession

from aiogram.fsm.context import FSMContext

from database.db import get_user_role
from enums.roles import UserRole

class UserService:
    @staticmethod
    async def get_role(
        session: AsyncSession,
        *,
        state: FSMContext,
        user_id: int
    ) -> UserRole:
        role_raw: str = await state.get_value("user_role")

        if role_raw:
            return UserRole(role_raw)

        user_role: UserRole = await get_user_role(session, user_id=user_id)

        return user_role