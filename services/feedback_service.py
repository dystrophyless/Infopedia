from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import add_search_feedback


class FeedbackService:
    @staticmethod
    async def add_feedback(
        session: AsyncSession,
        *,
        state: FSMContext,
        user_id: int,
        correct: bool,
    ):
        definition_id: int = await state.get_value("definition_id")
        query: str = await state.get_value("query")

        await add_search_feedback(
            session,
            user_id=user_id,
            definition_id=definition_id,
            query=query,
            correct=correct,
        )

        await state.update_data(definition_id=None, query=None, from_menu=None)
        await state.set_state()
