from aiogram.types import BotCommand
from enums.roles import UserRole

def get_main_menu_commands(i18n: dict[str, str], role: UserRole):
    if role == UserRole.USER or role == UserRole.CLIENT:
        return [
            BotCommand(
                command="/start",
                description=i18n.get("/start_description")
            ),
            BotCommand(
                command="/help",
                description=i18n.get("/help_description")
            ),
        ]
    elif role == UserRole.ADMIN:
        return [
            BotCommand(
                command="/start",
                description=i18n.get("/start_description")
            ),
            BotCommand(
                command="/help",
                description=i18n.get("/help_description")
            ),
            BotCommand(
                command="/stats",
                description=i18n.get("/stats_description")
            ),
            BotCommand(
                command="/feedback",
                description=i18n.get("/feedback_description")
            ),
            BotCommand(
                command="/ban",
                description=i18n.get("/ban_description")
            ),
            BotCommand(
                command="/unban",
                description=i18n.get("/unban_description")
            ),
        ]