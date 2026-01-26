from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from enums.roles import UserRole


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
                ),
                InlineKeyboardButton(
                    text=i18n.get("get_informed_about_roles_button"),
                    callback_data="get_informed_about_roles"
                )
            ]
        ]
    )


def build_buy_subscription_kb(i18n: dict, *, user_role: UserRole, back_to_profile: bool = False) -> InlineKeyboardMarkup | None:
    if user_role != UserRole.USER and not back_to_profile:
        return None

    buttons = []
    if user_role == UserRole.USER:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=i18n.get("buy_subscription_button"),
                    callback_data="buy_subscription"
                )
            ]
        )

    if back_to_profile:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=i18n.get("back_to_profile_menu_button"),
                    callback_data="back_to_profile_menu"
                )
            ]
        )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_buy_subscription_confirmation_kb(i18n: dict, *, back_to_get_informed_about_roles: bool = False) -> InlineKeyboardMarkup:
    buttons = []

    buttons.append(
        [
            InlineKeyboardButton(
                text=i18n.get("confirm_buy_subscription_button"),
                callback_data="confirm_buy_subscription"
            ),
        ]
    )

    if back_to_get_informed_about_roles:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=i18n.get("back_button"),
                    callback_data="get_informed_about_roles"
                )
            ]
        )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_back_kb(
    *,
    i18n: dict,
    callback_data: str
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=i18n.get("back_button"),
                    callback_data=callback_data
                )
            ]
        ]
    )


def build_process_subscription_receipt_kb(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Принять",
                    callback_data="approve_subscription"
                ),
                InlineKeyboardButton(
                    text="❌ Отклонить",
                    callback_data="reject_subscription"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⛔ Заблокировать пользователя",
                    callback_data=f"ban_user:{user_id}"
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

