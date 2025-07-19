import os

from aiogram import F, types
from aiogram.filters import Command, StateFilter, Filter
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from src.core.models.schema import UserProfileCreate
from src.core.states import Form
from src.keyborads.keyboards import create_inline_keyboard
from aiogram import Router

from aiogram.types import CallbackQuery, Message, KeyboardButton, ReplyKeyboardRemove
from src.servicies.database_manager import DatabaseManager

start_router = Router()
db = DatabaseManager()
user_states = {}
user_photo_cache = {}  # {user_id: [path1, path2]}
analysis_cache = {}

class WaitForTwoPhotos(Filter):
    async def __call__(self, message: Message) -> bool:
        return user_states.get(message.from_user.id) == "waiting_for_two_photos"

async def handle_start_or_back(
        event: types.Message | types.CallbackQuery,
        state: FSMContext
):
    builder = InlineKeyboardBuilder()

    keyboard_data = {
        "Анкета": "anketa",
        "Сравнение фото": "compare_two_photos",
        "Анализ диалога": "analyse_dialog"
    }
    create_inline_keyboard(builder=builder, data=keyboard_data)

    if not isinstance(event, types.CallbackQuery):
        await event.answer(
            "Добрый день! Я ваш ИИ-ментор по дейтингу. Выберите варианты:",
            reply_markup=builder.as_markup()
        )
    else:
        await state.clear()
        if event.message.photo is not None:
            await event.message.delete()
            await event.message.answer("Меню бота!", reply_markup=builder.as_markup())
        else:
            await event.message.edit_text("Меню бота!", reply_markup=builder.as_markup())


@start_router.message(Command("start"))
async def start_handler(message: Message, state: FSMContext):
    await handle_start_or_back(message, state)


@start_router.callback_query(F.data == "back")
async def back_handler(message: types.CallbackQuery, state: FSMContext):
    await handle_start_or_back(message, state)


@start_router.callback_query(F.data == "delete_a")
async def delete_anketa_handler(callback_query: CallbackQuery):
    await callback_query.answer()
    if db.delete_user_profile(callback_query.message.chat.id):
        await callback_query.message.delete()

        await (
            callback_query.
            message.
            answer(
                "Вы успешно удалили анкету!",
            )
        )

@start_router.callback_query(F.data == "analyse_dialog")
async def analyse_dialog_handler(callback_query: CallbackQuery):
    builder = InlineKeyboardBuilder()
    keyboard_data = {
        "HTML-файл": "html_history",
        "Скриншотом": "screen_history",
        "Назад к меню": "back"
    }
    create_inline_keyboard(builder=builder, data=keyboard_data)
    await callback_query.message.answer(
        "Выбери способ отправки диалога:",
        reply_markup=builder.as_markup()
    )

@start_router.callback_query(F.data == "anketa")
async def anketa_handler(callback_query: CallbackQuery, state: FSMContext):
    # await callback_query.message.delete()
    await callback_query.answer()

    chat_id = callback_query.message.chat.id
    profile = db.get_user_profile_by_user_id(chat_id)

    if profile is None:
        builder = InlineKeyboardBuilder()
        keyboard_data = {
            "Конструктором": "construct",
            "Скриншотом": "screen",
            "Назад к меню": "back"
        }
        create_inline_keyboard(builder=builder, data=keyboard_data)
        await callback_query.message.answer(
            "К сожалению у вас нет анкеты :(\nКак желаете ее заполнить?",
            reply_markup=builder.as_markup()
        )
        await state.set_state(Form.nickname)
    else:
        builder = InlineKeyboardBuilder()
        keyboard_data = {
            "Дать рекомендации": "recommending",
            "Прикрепить фото": "add_photo",
            "Удалить анкету": "delete_a",
            "Назад к меню": "back"
        }
        create_inline_keyboard(builder=builder, data=keyboard_data)
        if profile.img_id is None:
            await callback_query.message.edit_text(
                f"Ваша анкета:\n"
                f"Ник: {profile.name}\n"
                f"Возраст: {profile.age}\n"
                f"О себе: {profile.about}\n"
                f"Доп факты: {profile.meta}",
                reply_markup=builder.as_markup()
            )
        else:
            await callback_query.message.answer_photo(
                photo=profile.img_id,
                caption=f"Ваша анкета:\n"
                        f"Ник: {profile.name}\n"
                        f"Возраст: {profile.age}\n"
                        f"О себе: {profile.about}\n"
                        f"Доп факты: {profile.meta}",
                reply_markup=builder.as_markup()
            )

@start_router.callback_query(F.data == "screen")
async def analyse_screen_handler(callback_query: CallbackQuery, state: FSMContext):
    pass

@start_router.callback_query(F.data == "construct")
async def start_construct(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите свое имя:")
    await state.set_state(Form.nickname)


@start_router.message(Form.nickname)
async def process_nickname(message: Message, state: FSMContext):
    await state.update_data(nickname=message.text)
    await state.set_state(Form.age)
    await message.answer("Введите свой возраст:")


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
    await state.set_state(Form.about)
    await message.answer("Введите информацию о себе:")


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

    builder = InlineKeyboardBuilder()
    keyboard_data = {
        "Дать рекомендации": "recommending",
        "Прикрепить фото": "add_photo",
        "Удалить анкету": "delete_a",
        "Назад к меню": "back"
    }
    create_inline_keyboard(builder=builder, data=keyboard_data)
    await message.answer(
        f"Спасибо!\n"
        f"Ваша анкета:\n"
        f"Ник: {profile.name}\n"
        f"Возраст: {profile.age}\n"
        f"О себе: {profile.about}\n"
        f"Доп факты: {profile.meta}",
        reply_markup=builder.as_markup(),
    )
    await state.clear()


@start_router.callback_query(F.data == 'add_photo')
async def add_photo_handler(callback: CallbackQuery, state: FSMContext):
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="Отменить отправку фото", callback_data="back_to_anketa"))

    # Отправляем сообщение с клавиатурой
    await callback.message.answer(
        "Отправьте фото в чат",
        reply_markup=builder.as_markup(resize_keyboard=True, one_time_keyboard=True)
    )
    await state.set_state("waiting_for_photo")  # Устанавливаем состояние
    await callback.answer()


@start_router.callback_query(F.data == 'back_to_anketa')
async def back_to_anketa_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()  # Очищаем состояние
    await callback.message.delete()  # Удаляем сообщение "Отправьте своё фото"
    await callback.answer("Добавление фото отменено", show_alert=False)

    # Здесь вызываем функцию, которая показывает анкету снова
    await anketa_handler(callback, state)


@start_router.message(F.photo, StateFilter("waiting_for_photo"))
async def process_img(message: Message, state: FSMContext):
    await message.answer("Загрузка профиля...", reply_markup=ReplyKeyboardRemove())

    # Получаем данные пользователя
    chat_id = message.chat.id
    profile = db.update_user_profile(chat_id, message.photo[-1].file_id)
    await message.delete()

    # Создаём клавиатуру
    builder = InlineKeyboardBuilder()
    keyboard_data = {
        "Дать рекомендации": "recommending",
        "Прикрепить фото": "add_photo",
        "Удалить анкету": "delete_a",
        "Назад к меню": "back"
    }
    create_inline_keyboard(builder=builder, data=keyboard_data)

    # Отправляем фото обратно с анкетой
    await message.answer_photo(
        photo=profile.img_id,
        caption=f"Спасибо!\n"
                f"Ваша анкета:\n"
                f"Ник: {profile.name}\n"
                f"Возраст: {profile.age}\n"
                f"О себе: {profile.about}\n"
                f"Доп факты: {profile.meta}",
        reply_markup=builder.as_markup()
    )

    await state.clear()
