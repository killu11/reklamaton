import asyncio
import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from core.dependecies import bot, dp

router = Router()
dp.include_router(router)

logging.basicConfig(
    level=logging.INFO,
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

@router.message()
async def unknown_message(message: Message):
    await message.answer("Извините, я не понимаю это сообщение.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())