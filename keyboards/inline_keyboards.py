from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from utils.callback_factories import SourceCallback, TermCallback
from enums.grades import UserGrade


def build_language_kb(i18n: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=i18n.get("kz"),
                    callback_data="kz"
                ),
                InlineKeyboardButton(
                    text=i18n.get("ru"),
                    callback_data="ru"
                )
            ]
        ]
    )


def build_language_settings_kb(i18n: dict, locales: list[str], checked: str) -> InlineKeyboardMarkup:
    buttons = []
    for locale in sorted(locales):
        if locale == "default":
            continue
        if locale == checked:
            buttons.append(
                [
                    InlineKeyboardButton(
                        text=f"🔘 {i18n.get(locale)}",
                        callback_data=locale
                    )
                ]
            )
        else:
            buttons.append(
                [
                    InlineKeyboardButton(
                        text=f"⚪️ {i18n.get(locale)}",
                        callback_data=locale
                    )
                ]
            )
    buttons.append(
        [
            InlineKeyboardButton(
                text=i18n.get("cancel_language_button_text"),
                callback_data="cancel_language_button_data"
            ),
            InlineKeyboardButton(
                text=i18n.get("save_language_button_text"),
                callback_data="save_language_button_data"
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_grade_kb(i18n: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=i18n.get(UserGrade.GRADE_11),
                    callback_data=UserGrade.GRADE_11
                ),
                InlineKeyboardButton(
                    text=i18n.get(UserGrade.GRADE_10),
                    callback_data=UserGrade.GRADE_10
                )
            ],
            [
                InlineKeyboardButton(
                    text=i18n.get(UserGrade.GRADE_IDK),
                    callback_data=UserGrade.GRADE_UNDEFINED
                )
            ]
        ]
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
                    callback_data="check_membership"
                )
            ]
        ]
    )


def build_search_kb(i18n: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=i18n.get("search_button"),
                    switch_inline_query_current_chat=""
                )
            ]
        ]
    )


def build_suggestion_kb(i18n: dict, suggested_definition: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=i18n.get("suggestion_positive_reply_button"),
                    callback_data=f"suggestion_positive_reply:{suggested_definition}"
                ),
                InlineKeyboardButton(
                    text=i18n.get("suggestion_negative_reply_button"),
                    callback_data="suggestion_negative_reply"
                )
            ]
        ]
    )


def build_suggestion_decision_kb(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Принять",
                    callback_data="add_new_definition"
                ),
                InlineKeyboardButton(
                    text="❌ Отклонить",
                    callback_data="deny_new_definition"
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


def build_sources_kb(term: str, terms: dict, term_names_to_ids: dict[str, int], source_names_to_ids: dict[str, int], current_source_name: str = "Алматыкітап: 7-сынып", current_index: int = 0) -> InlineKeyboardMarkup:
    kb_builder = InlineKeyboardBuilder()

    sources = terms[term]

    source_names = list(sources.keys())
    first_source_name, first_source_entries = next(iter(sources.items()))

    total_indexes = len(first_source_entries)

    term_id = term_names_to_ids[term]

    for source_name in source_names:
        source_id = source_names_to_ids[source_name]

        if source_name == current_source_name:
            kb_builder.button(
                text=f"✅ {source_name}",
                callback_data="noop"
            )
        else:
            kb_builder.button(
                text=source_name,
                callback_data=SourceCallback(term=term_id, source=source_id).pack()
            )

    nav_row = []

    source_id = source_names_to_ids[current_source_name]

    if total_indexes > 1:
        if current_index > 0:
            nav_row.append(
                InlineKeyboardButton(
                    text="◀ Предыдущее",
                    callback_data=TermCallback(term=term_id, source=source_id, index=current_index-1).pack()
                )
            )

        nav_row.append(
            InlineKeyboardButton(
                text=f"{current_index + 1}/{total_indexes}",
                callback_data="noop"
            )
        )

        if current_index < total_indexes - 1:
            nav_row.append(
                InlineKeyboardButton(
                    text="Следующее ▶",
                    callback_data=TermCallback(term=term_id, source=source_id, index=current_index+1).pack()
                )
            )

        if nav_row:
            kb_builder.row(*nav_row)

    kb_builder.adjust(len(source_names), len(nav_row))

    return kb_builder.as_markup()


