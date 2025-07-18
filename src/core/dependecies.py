from typing import Tuple

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from src.core.config import Settings, settings
from src.handlers import all_routers

def get_bot_with_dp(settings: Settings) -> Tuple[Bot, Dispatcher]:
    bot = Bot(token=settings.token)
    dp = Dispatcher(bot=bot, storage=MemoryStorage())

    for router in all_routers:
        dp.include_router(router)

    return bot, dp

bot, dp = get_bot_with_dp(settings)
