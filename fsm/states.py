from aiogram.fsm.state import State, StatesGroup

class FSMRegister(StatesGroup):
    await_membership = State()
    choose_language = State()
    choose_grade = State()
    choose_update_on_news = State()


class FSMLanguage(StatesGroup):
    choose_language = State()


class FSMMembership(StatesGroup):
    await_membership = State()


class FSMSearch(StatesGroup):
    await_definition_to_recognize = State()
    await_considering_definition = State()