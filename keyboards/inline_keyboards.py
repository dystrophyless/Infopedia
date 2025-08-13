from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from utils.callback_factories import SourceCallback, TermCallback



def build_language_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='🇰🇿 Казахский',
                    callback_data='kz'
                ),
                InlineKeyboardButton(
                    text='🇷🇺 Русский',
                    callback_data='ru'
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
            #print(i18n.get(locale))
            buttons.append(
                [
                    InlineKeyboardButton(
                        text=f"🔘 {i18n.get(locale)}",
                        callback_data=locale
                    )
                ]
            )
        else:
            #print(i18n.get(locale))
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


def build_grade_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='11 класс',
                    callback_data='grade_11'
                ),
                InlineKeyboardButton(
                    text='10 класс',
                    callback_data='grade_10'
                )
            ],
            [
                InlineKeyboardButton(
                    text='🤷🏻 Без понятия',
                    callback_data='grade_undefined'
                )
            ]
        ]
    )


def build_update_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='🔔 Да, получать новости',
                    callback_data='get_updated_on_news'
                ),
                InlineKeyboardButton(
                    text='🔕 Нет, не нужно',
                    callback_data='do_not_get_updated_on_news'
                )
            ]
        ]
    )


def build_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='👤 Профиль',
                    callback_data='profile_menu'
                ),
                InlineKeyboardButton(
                    text='🏠 Главная',
                    callback_data='main_menu'
                )
            ]
        ]
    )

def build_channel_kb(invite_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='🔔 Подписаться',
                    url=invite_url,
                ),
                InlineKeyboardButton(
                    text='⏳ Проверить подписку',
                    callback_data='check_channel_subscription'
                )
            ]
        ]
    )

def build_search_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='🔍 Поиск термина',
                    switch_inline_query_current_chat=''
                )
            ]
        ]
    )

def build_suggestion_kb(suggested_definition: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='✅ Да, хочу',
                    callback_data=f'suggestion_positive_reply:{suggested_definition}'
                ),
                InlineKeyboardButton(
                    text='❌ Нет, не хочу',
                    callback_data='suggestion_negative_reply'
                )
            ]
        ]
    )

def build_suggestion_decision_kb(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='✅ Принять',
                    callback_data='add_new_definition'
                ),
                InlineKeyboardButton(
                    text='❌ Отклонить',
                    callback_data='delete'
                )
            ],
            [
                InlineKeyboardButton(
                    text='⛔ Заблокировать пользователя',
                    callback_data=f'ban_user:{user_id}'
                )
            ]
        ]
    )

def build_sources_kb(term: str, terms: dict, term_names_to_ids: dict[str, int], source_names_to_ids: dict[str, int], current_source_name: str = 'Алматыкітап: 7-сынып', current_index: int = 0) -> InlineKeyboardMarkup:
    kb_builder = InlineKeyboardBuilder()

    sources = terms[term]

    source_names = list(sources.keys())
    first_source_name, first_source_entries = next(iter(sources.items()))

    total_indexes = len(first_source_entries)

    term_id = term_names_to_ids[term]

    for source_name in source_names:
        source_id = source_names_to_ids[source_name]

        if source_name == current_source_name:
            # Текущий выбранный источник — пассивная кнопка
            kb_builder.button(
                text=f"✅ {source_name}",
                callback_data="noop"
            )
        else:
            # Остальные — активные кнопки
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
                callback_data="noop"  # или заглушка, чтоб ничего не делал
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


