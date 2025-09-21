from aiogram.filters.callback_data import CallbackData

class SourceCallback(CallbackData, prefix='source'):
    term_id: int
    source_id: int


class TermCallback(CallbackData, prefix='term'):
    term_id: int
    source_id: int
    index: int