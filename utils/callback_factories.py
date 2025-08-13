from aiogram.filters.callback_data import CallbackData

class SourceCallback(CallbackData, prefix='source'):
    term: int
    source: int


class TermCallback(CallbackData, prefix='term'):
    term: int
    source: int
    index: int