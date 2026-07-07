from aiogram import Router, types
from aiogram.filters import Command

router = Router()

@router.message(Command("text"))
async def cmd_text(message: types.Message):
    """Обработчик команды /text (заглушка)"""
    await message.answer(
        "📝 Команда /text будет реализована позже.\n"
        "Здесь будет функционал для преобразования текста."
    )