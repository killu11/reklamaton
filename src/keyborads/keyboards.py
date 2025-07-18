from typing import Dict

from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def create_inline_keyboard(
        builder: InlineKeyboardBuilder,
        data: Dict[str, str]
) -> None:

    for button_text, callback in data.items():
        builder.add(InlineKeyboardButton(text=button_text, callback_data=callback))
    builder.adjust(2)

def create_reply_keyboard():
    pass
