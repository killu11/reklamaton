from typing import Tuple

from aiogram import Bot, Dispatcher
from src.core.config import Settings, settings

def get_bot_with_dp(settings: Settings) -> Tuple[Bot, Dispatcher]:
    return Bot(token=settings.token), Dispatcher()

bot, dp = get_bot_with_dp(settings)

