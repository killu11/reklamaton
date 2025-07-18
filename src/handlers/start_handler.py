from importlib.metadata import metadata

from aiogram import F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
# from ..core.dependecies import db

from src.core.states import Form
from src.keyborads.keyboards import create_inline_keyboard
from aiogram import Router

from aiogram.types import CallbackQuery, Message
from src.servicies.database_manager import DatabaseManager
from src.servicies.schema import UserProfileCreate

start_router = Router()
db = DatabaseManager()


@start_router.message(Command("start"))
async def start_handler(message: Message):
    builder = InlineKeyboardBuilder()
    data = {
        "Оценка анкеты": "anketa",
        "Анализ диалога": "analyse_dialog"
    }

    create_inline_keyboard(builder=builder, data=data)

    await message.answer("Добрый день! Я ваш ИИ-ментор по дейтингу. Выберите варианты:", reply_markup=builder.as_markup())


@start_router.callback_query(F.data == "anketa")
async def anketa_handler(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()

    chat_id = callback_query.message.chat.id
    profile = db.get_user_profile_by_user_id(chat_id)

    if profile is None:
        await callback_query.message.answer("Введите свой ник:")
        await state.set_state(Form.nickname)
        return
    else:
        await callback_query.message.answer(
            f"Спасибо!\n"
            f"Ваша анкета:\n"
            f"Ник: {profile.name}\n"
            f"Возраст: {profile.age}\n"
            f"О себе: {profile.about}\n"
            f"Доп факты: {profile.meta}"
        )


@start_router.message(Form.nickname)
async def process_nickname(message: Message, state: FSMContext):
    await state.update_data(nickname=message.text)
    await message.answer("Введите свой возраст:")

    await state.set_state(Form.age)


@start_router.message(Form.age)
async def process_age(message: Message, state: FSMContext):
    age_text = message.text

    # Проверяем, является ли ввод числом
    if not age_text.isdigit():
        await message.answer("Пожалуйста, введите возраст числом.")
        return

    age = int(age_text)

    # Проверяем диапазон
    if age < 14 or age > 120:
        await message.answer("Пожалуйста, введите корректный возраст (от 14 до 120).")
        return

    await state.update_data(age=message.text)
    await message.answer("Введите информацию о себе:")
    await state.set_state(Form.about)


@start_router.message(Form.about)
async def process_about(message: Message, state: FSMContext):
    await state.update_data(about=message.text)

    data = await state.get_data()
    nickname = data["nickname"]
    age = data["age"]
    about = data["about"]

    user = UserProfileCreate(
        user_id=message.chat.id,
        name=nickname,
        age=age,
        about=about,
        gender="M",
        meta={'city': 'moscow'}
    )

    profile = db.create_user_profile(user)

    await message.answer(
        f"Спасибо!\n"
        f"Ваша анкета:\n"
        f"Ник: {profile.name}\n"
        f"Возраст: {profile.age}\n"
        f"О себе: {profile.about}\n"
        f"Доп факты: {profile.meta}"
    )
    await state.clear()
