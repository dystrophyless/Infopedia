from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def build_menu_kb(i18n: dict) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text=i18n.get("profile_menu_button"),
                    callback_data="profile_menu"
                ),
                KeyboardButton(
                    text=i18n.get("main_menu_button"),
                    callback_data="main_menu"
                )
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )


def build_profile_menu_kb(i18n: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=i18n.get("change_language_button"),
                    callback_data="change_language"
                )
            ]
        ]
    )


def build_main_menu_kb(i18n: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=i18n.get("get_random_term_button"),
                    callback_data="get_random_term"
                ),
                InlineKeyboardButton(
                    text=i18n.get("search_button"),
                    callback_data="search"
                )
            ],
        ]
    )