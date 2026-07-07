import re
from aiogram import Router, types
from aiogram.filters import Command
from database.db import get_publications_by_ids, update_publication_text
from services.text_extractor import extract_text_from_url
import asyncio

router = Router()

@router.message(Command("processing"))
async def cmd_processing(message: types.Message):
    """Обработчик команды /processing"""
    # Получаем аргументы команды
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "⚠️ Укажите ID через запятую. Пример: <code>/processing 1, 2, 3</code>", 
            parse_mode="HTML"
        )
        return
    
    # Парсим ID
    raw_ids = re.sub(r'[^\d,]', '', args[1])
    try:
        ids = [int(x) for x in raw_ids.split(',') if x]
    except ValueError:
        await message.answer("⚠️ Ошибка формата ID.")
        return
    
    if not ids:
        await message.answer("⚠️ Не найдено ни одного валидного ID.")
        return
    
    await message.answer(f"⏳ Начинаю обработку {len(ids)} публикаций...")
    
    # Получаем данные из БД
    publications = await get_publications_by_ids(ids)
    found_ids = {p['id'] for p in publications}
    missing_ids = set(ids) - found_ids
    
    success_count = 0
    errors = []
    
    # Обрабатываем каждую публикацию
    for pub in publications:
        try:
            text = await extract_text_from_url(pub['url'])
            await update_publication_text(pub['id'], text)
            success_count += 1
        except Exception as e:
            errors.append(f"ID {pub['id']}: {str(e)[:100]}")
    
    # Формируем отчёт
    report = f"✅ Обработка завершена!\n\n"
    report += f"📊 Успешно обработано: {success_count}\n"
    report += f"❌ Ошибок: {len(errors)}"
    
    if missing_ids:
        report += f"\n\n⚠️ ID не найдены в БД: {', '.join(map(str, missing_ids))}"
    
    if errors:
        report += f"\n\n<b>Детали ошибок:</b>\n"
        for error in errors[:5]:  # Показываем первые 5 ошибок
            report += f"• {error}\n"
        if len(errors) > 5:
            report += f"\n... и ещё {len(errors) - 5} ошибок"
    
    await message.answer(report, parse_mode="HTML")