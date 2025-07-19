from aiogram.fsm.state import State, StatesGroup

class Form(StatesGroup):
    img = State() ## путь до файла
    nickname = State()
    age = State()
    about = State()
