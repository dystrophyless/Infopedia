from aiogram.fsm.state import State, StatesGroup

class FSMRegister(StatesGroup):
    start_register = State()
    await_membership = State()
    choose_language = State()
    choose_grade = State()
    choose_update_on_news = State()

class FSMMembership(StatesGroup):
    await_membership = State()

class FSMLanguage(StatesGroup):
    choose_language = State()