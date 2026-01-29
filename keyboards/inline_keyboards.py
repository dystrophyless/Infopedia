from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.models import Source, Term
from enums.grades import UserGrade
from utils.callback_factories import TermCallback


def build_language_kb(i18n: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=i18n.get("kz"), callback_data="kz"),
                InlineKeyboardButton(text=i18n.get("ru"), callback_data="ru"),
            ],
        ],
    )


def build_language_settings_kb(
    i18n: dict,
    locales: list[str],
    checked: str,
) -> InlineKeyboardMarkup:
    buttons = []
    for locale in sorted(locales):
        if locale == "default":
            continue
        if locale == checked:
            buttons.append(
                [
                    InlineKeyboardButton(
                        text=f"🔘 {i18n.get(locale)}",
                        callback_data=locale,
                    ),
                ],
            )
        else:
            buttons.append(
                [
                    InlineKeyboardButton(
                        text=f"⚪️ {i18n.get(locale)}",
                        callback_data=locale,
                    ),
                ],
            )
    buttons.append(
        [
            InlineKeyboardButton(
                text=i18n.get("back_to_profile_menu_button"),
                callback_data="back_to_profile_menu",
            ),
            InlineKeyboardButton(
                text=i18n.get("save_language_button"),
                callback_data="save_language_button_data",
            ),
        ],
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_grade_kb(i18n: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=i18n.get(UserGrade.GRADE_11),
                    callback_data=UserGrade.GRADE_11,
                ),
                InlineKeyboardButton(
                    text=i18n.get(UserGrade.GRADE_10),
                    callback_data=UserGrade.GRADE_10,
                ),
            ],
            [
                InlineKeyboardButton(
                    text=i18n.get(UserGrade.GRADE_UNDEFINED),
                    callback_data=UserGrade.GRADE_UNDEFINED,
                ),
            ],
        ],
    )


def build_channel_kb(i18n: dict, invite_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=i18n.get("follow_button"),
                    url=invite_url,
                ),
                InlineKeyboardButton(
                    text=i18n.get("check_membership_button"),
                    callback_data="check_membership",
                ),
            ],
        ],
    )


def build_search_kb(
    i18n: dict,
    *,
    back_to_main_menu: bool = False,
) -> InlineKeyboardMarkup:
    buttons = []

    buttons.append(
        [
            InlineKeyboardButton(
                text=i18n.get("find_term_by_name_button"),
                switch_inline_query_current_chat="",
            ),
            InlineKeyboardButton(
                text=i18n.get("find_term_by_definition_button"),
                callback_data="find_term_by_definition",
            ),
        ],
    )

    if back_to_main_menu:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=i18n.get("back_to_main_menu_button"),
                    callback_data="back_to_main_menu",
                ),
            ],
        )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_considering_definition_kb(i18n: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=i18n.get("definition_was_exact_button"),
                    callback_data="definition_was_exact",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=i18n.get("definition_was_not_exact_button"),
                    callback_data="definition_was_not_exact",
                ),
            ],
        ],
    )


def build_repeating_search_definition_kb(i18n: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=i18n.get("repeat_search_definition_button"),
                    callback_data="find_term_by_definition",
                ),
            ],
        ],
    )


def build_suggestion_kb(i18n: dict, suggested_term: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=i18n.get("suggestion_positive_reply_button"),
                    callback_data=f"suggestion_positive_reply:{suggested_term}",
                ),
                InlineKeyboardButton(
                    text=i18n.get("suggestion_negative_reply_button"),
                    callback_data="suggestion_negative_reply",
                ),
            ],
        ],
    )


def build_suggestion_decision_kb(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Принять", callback_data="add_new_term"),
                InlineKeyboardButton(
                    text="❌ Отклонить",
                    callback_data="deny_new_term",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⛔ Заблокировать пользователя",
                    callback_data=f"ban_user:{user_id}",
                ),
            ],
        ],
    )


def build_sources_kb(
    *,
    term: Term,
    current_source: Source,
    current_index: int = 0,
) -> InlineKeyboardMarkup:
    kb_builder = InlineKeyboardBuilder()

    sources: list[Source] = term.sources

    total_indexes = len(current_source.definitions)

    for source in sources:
        if source.name == current_source.name:
            kb_builder.row(
                InlineKeyboardButton(text=f"✅ {source.name}", callback_data="noop"),
            )
        else:
            kb_builder.row(
                InlineKeyboardButton(
                    text=source.name,
                    callback_data=TermCallback(
                        term_id=term.id,
                        source_id=source.id,
                        index=0,
                    ).pack(),
                ),
            )

    nav_row = []

    if total_indexes > 1:
        if current_index > 0:
            nav_row.append(
                InlineKeyboardButton(
                    text="◀ Предыдущее",
                    callback_data=TermCallback(
                        term_id=term.id,
                        source_id=current_source.id,
                        index=current_index - 1,
                    ).pack(),
                ),
            )

        nav_row.append(
            InlineKeyboardButton(
                text=f"{current_index + 1}/{total_indexes}",
                callback_data="noop",
            ),
        )

        if current_index < total_indexes - 1:
            nav_row.append(
                InlineKeyboardButton(
                    text="Следующее ▶",
                    callback_data=TermCallback(
                        term_id=term.id,
                        source_id=current_source.id,
                        index=current_index + 1,
                    ).pack(),
                ),
            )

        if nav_row:
            kb_builder.row(*nav_row)

    return kb_builder.as_markup()
