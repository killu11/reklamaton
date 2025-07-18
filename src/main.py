import asyncio
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import Message


# Создаем бота и диспетчер
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Создаем роутер (можно разносить по файлам при росте проекта)
router = Router()

# Хендлер на команду /start
@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Привет! Это базовый Telegram-бот на aiogram 3.x")

# Хендлер на любое текстовое сообщение
@router.message()
async def echo_message(message: Message):
    await message.answer(f"Вы написали: {message.text}")

# Регистрируем роутер в диспетчере
dp.include_router(router)

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())