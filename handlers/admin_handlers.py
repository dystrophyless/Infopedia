import logging

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, CommandObject

from sqlalchemy.ext.asyncio import AsyncSession

from enums.roles import UserRole
from schemas.user import UserStat
from schemas.feedback import FeedbackStat
from filters.filters import UserRoleFilter
from database.db import (
    get_activity_statistics_individually,
    get_user_banned_status_by_id,
    get_user_banned_status_by_username,
    change_user_banned_status_by_id,
    change_user_banned_status_by_username,
    get_search_statistics_individually,
    get_search_statistics_generally,
    get_activity_statistics_generally,
)

logger = logging.getLogger(__name__)

router = Router()

router.message.filter(UserRoleFilter(UserRole.ADMIN))
router.callback_query.filter(UserRoleFilter(UserRole.ADMIN))


@router.message(Command(commands=["help"]))
async def process_admin_help_command(message: Message, i18n: dict):
    await message.answer(text=i18n.get("/help_admin"))


@router.message(Command(commands=["stats"]))
async def process_admin_statistics_command(
    message: Message, session: AsyncSession, i18n: dict
):
    statistics: list[UserStat] = await get_activity_statistics_individually(session)
    total_actions = await get_activity_statistics_generally(session)

    if statistics:
        await message.answer(
            text=i18n.get("/stats").format(
                info_rows="\n".join(
                    f"{i}. {stat.link}: {stat.total_actions}"
                    for i, stat in enumerate(statistics, 1)
                ),
                total_actions=total_actions,
            )
        )
    else:
        await message.answer(text=i18n.get("stats_were_not_found"))


@router.message(Command(commands=["feedback"]))
async def process_admin_feedback_command(
    message: Message, session: AsyncSession, i18n: dict
):
    statistics: list[FeedbackStat] = await get_search_statistics_individually(session)
    total_queries, total_accuracy = await get_search_statistics_generally(session)

    if statistics:
        await message.answer(
            text=i18n.get("/feedback").format(
                info_rows="\n".join(
                    f"{i}. №{feedback.definition_id}: {feedback.short_term_name} [{feedback.correct_queries}/{feedback.total_queries}] (~{feedback.accuracy}%)"
                    for i, feedback in enumerate(statistics, 1)
                ),
                total_queries=total_queries,
                total_accuracy=f"~{total_accuracy}%",
            )
        )
    else:
        await message.answer(text=i18n.get("feedback_was_not_found"))


@router.message(Command(commands=["ban"]))
async def process_admin_ban_command(
    message: Message, command: CommandObject, session: AsyncSession, i18n: dict
):
    args = command.args

    if not args:
        await message.reply(text=i18n.get("empty_ban_answer"))
        return

    arg_user = args.split()[0].strip()

    if arg_user.isdigit():
        banned_status = await get_user_banned_status_by_id(
            session, user_id=int(arg_user)
        )
    elif arg_user.startswith("@"):
        banned_status = await get_user_banned_status_by_username(
            session, username=arg_user[1:]
        )
    else:
        await message.reply(text=i18n.get("incorrect_ban_argument"))
        return

    if banned_status is None:
        await message.reply(i18n.get("no_user"))
    elif banned_status:
        await message.reply(i18n.get("already_banned"))
    else:
        if arg_user.isdigit():
            await change_user_banned_status_by_id(
                session, user_id=int(arg_user), banned=True
            )
        else:
            await change_user_banned_status_by_username(
                session, username=arg_user[1:], banned=True
            )

        await message.reply(text=i18n.get("successfully_banned"))


@router.message(Command(commands=["unban"]))
async def process_admin_unban_command(
    message: Message, command: CommandObject, session: AsyncSession, i18n: dict
):
    args = command.args

    if not args:
        await message.reply(text=i18n.get("empty_ban_answer"))
        return

    arg_user = args.split()[0].strip()

    if arg_user.isdigit():
        banned_status = await get_user_banned_status_by_id(
            session, user_id=int(arg_user)
        )
    elif arg_user.startswith("@"):
        banned_status = await get_user_banned_status_by_username(
            session, username=arg_user[1:]
        )
    else:
        await message.reply(text=i18n.get("incorrect_unban_argument"))
        return

    if banned_status is None:
        await message.reply(i18n.get("no_user"))
    elif banned_status:
        if arg_user.isdigit():
            await change_user_banned_status_by_id(
                session, user_id=int(arg_user), banned=False
            )
        else:
            await change_user_banned_status_by_username(
                session, username=arg_user[1:], banned=False
            )

        await message.reply(text=i18n.get("successfully_unbanned"))
    else:
        await message.reply(i18n.get("not_banned"))
