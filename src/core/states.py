from aiogram.fsm.state import State, StatesGroup

class Form(StatesGroup):
    nickname = State()
    age = State()
    about = State()
