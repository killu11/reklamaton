import asyncio
import logging

from aiogram import Router
from src.core.dependecies import bot, dp

router = Router()

logging.basicConfig(
    level=logging.INFO,
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(e)
