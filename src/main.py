import asyncio
import json
import logging
import os
import tempfile

import httpx
from aiogram import Router, F
from aiogram.filters import StateFilter, Filter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, Document, FSInputFile

from core.dependecies import bot, dp, clean_text
from src.handlers.start_handler import db, user_photo_cache, analysis_cache, user_states
from src.servicies.parser import parse_twinby_chat, parse_telegram_html_chat
from src.servicies.photo_analyzer import analyze_single_photo, compare_two_photos

main_router = Router()
PHOTO_DIR = "imgs"
API = "https://9a47d9ea5108.ngrok-free.app/analyze"

class WaitForTwoPhotos(Filter):
    async def __call__(self, message: Message) -> bool:
        return user_states.get(message.from_user.id) == "waiting_for_two_photos"

@main_router.callback_query(F.data == "recommending")
async def recommends(callback_query: CallbackQuery):
    user_id = callback_query.message.chat.id
    profile = db.get_user_profile_by_user_id(user_id)

    try:
        file = await bot.get_file(profile.img_id)
        path = f"imgs/{profile.img_id}.jpg" if profile.img_id else None

        if not os.path.exists(path):
            await bot.download_file(file.file_path, f"imgs/{profile.img_id}.jpg")

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, analyze_single_photo, path
        )

        async with httpx.AsyncClient(timeout=100) as client:
            response = await client.post(
                API,
                json={"text": profile.about, "task_type": "profile"},
                headers={
                    "Content-Type": "application/json",
                    # Опционально: убрать предупреждение ngrok
                    "ngrok-skip-browser-warning": "true"
                }
            )
            response.raise_for_status()
            analyse_res_text = response.json()  # Получаем результат

        if "error" in result:
            await callback_query.message.answer(result["error"])
        else:
            text = "✅ Анализ завершён!\n\n"
            text += "📌 Рекомендации:\n"
            for rec in result["recommendations"]:
                text += f"{rec}\n"
            await callback_query.message.answer(f"{text}\n\n{analyse_res_text}", parse_mode="Markdown")

        if os.path.exists(path):
            os.remove(path)

    except Exception as e:
        logging.error(f"Ошибка при анализе фото: {e}", exc_info=True)
        await callback_query.message.answer(
            "❌ К сожалению, возникла ошибка при анализе данных анкеты. Попробуйте снова.")

@main_router.callback_query(F.data == "screen_history")
async def screen_history_start(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.answer("Отправьте скриншот переписки:")
    await state.set_state("waiting_for_screen")

@main_router.message(F.photo, StateFilter("waiting_for_screen"))
async def screen_history_analyse(message: Message, state: FSMContext):
    text = ''
    photo = message.photo[-1]
    file_id = photo.file_id
    photo_path = os.path.join(PHOTO_DIR, f"{file_id}.jpg")
    await message.answer("⚙️ Сохраняю и анализирую скриншот чата...")
    try:
        file = await bot.get_file(file_id)
        await bot.download(file, destination=photo_path)
        loop = asyncio.get_event_loop()
        messages = await loop.run_in_executor(
            None, parse_twinby_chat, photo_path
        )

        for msg in messages:
            text += f"<b>{msg['role']}:</b> {msg['text']}\n"

        async with httpx.AsyncClient(timeout=100) as client:
            response = await client.post(
                API,
                json={"text": text, "task_type": "dialog"},
                headers={
                    "Content-Type": "application/json",
                    # Опционально: убрать предупреждение ngrok
                    "ngrok-skip-browser-warning": "true"
                }
            )
            response.raise_for_status()
            analyse_res_text = response.json()['response']
            res = clean_text(analyse_res_text)

            await message.answer(res, parse_mode="Markdown")

    except Exception as e:
        logging.error(f"Ошибка: {e}", exc_info=True)
        await message.answer("❌ К сожалению, возникла ошибка при анализе чата.")
    finally:
        if os.path.exists(photo_path):
            os.remove(photo_path)

@main_router.callback_query(F.data == "html_history")
async def screen_history_start(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.answer("Отправьте html документ:")
    await state.set_state("waiting_for_html")

@main_router.message(F.document, StateFilter("waiting_for_html"))
async def html_chat_handler(message: Message):
    user_id = message.from_user.id
    document: Document = message.document
    file_name = document.file_name
    # Проверяем что прислали действительно html
    if not (file_name and file_name.lower().endswith(".html")):
        await message.answer("Пожалуйста, пришлите правильный файл messages.html.")
        return
    file_path = os.path.join(PHOTO_DIR, f"{user_id}_{file_name}")
    await message.answer("⚙️ Сохраняю и анализирую HTML чат...")
    try:
        file = await bot.get_file(document.file_id)
        await bot.download(file, destination=file_path)
        loop = asyncio.get_event_loop()
        messages = await loop.run_in_executor(
            None, parse_telegram_html_chat, file_path
        )
        user_states[user_id] = None
        # -- PREVIEW текстом --
        preview_lines = "\n".join(
            [f"<b>{m['role']}:</b> {m['text']}" for m in messages]
        )

        async with httpx.AsyncClient(timeout=300) as client:
            response = await client.post(
                API,
                json={"text": preview_lines, "task_type": "dialog"},
                headers={
                    "Content-Type": "application/json",
                    # Опционально: убрать предупреждение ngrok
                    "ngrok-skip-browser-warning": "true"
                }
            )
            response.raise_for_status()
            analyse_res_text = response.json()['response']
            res = clean_text(analyse_res_text)

            await message.answer(res, parse_mode="Markdown")

    except Exception as e:
        logging.error(f"Ошибка парсинга html-чата: {e}", exc_info=True)
        await message.answer("❌ Ошибка при обработке файла.")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

logging.basicConfig(
    level=logging.INFO,
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


async def main():
    dp.include_router(main_router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(e)
