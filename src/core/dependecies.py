import re
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

def clean_text(response: str) -> str:
    pattern = r"1\.\s*\*\*Анализ анкеты\*\*:.*?(?=\n\s*2\.\s*\*\*Рекомендации\*\*:)"
    match = re.search(pattern, response, re.DOTALL)
    if match:
        # Находим начало анализа
        start_index = match.start()
        # Извлекаем весь текст от начала анализа до конца
        response_from_analysis = response[start_index:]
        # Удаляем возможное дублирование пустой структуры формата в начале
        response_cleaned = re.sub(r"1\.\s*\*\*Анализ анкеты\*\*.*?\n\s*2\.\s*\*\*Рекомендации\*\*.*?\n\s*3\.\s*\*\*Объяснение\*\*.*?\n\s*(?=1\.\s*\*\*Анализ)", "", response_from_analysis, flags=re.DOTALL)
        return response_cleaned.strip()
    else:
        # Если формат не найден, возвращаем весь текст, очищенный от пробелов
        return response.strip()