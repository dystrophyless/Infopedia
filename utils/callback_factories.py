from aiogram.filters.callback_data import CallbackData


class TermCallback(CallbackData, prefix="term"):
    term_id: int
    book_id: int
    index: int
