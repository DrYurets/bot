from aiogram import Router, types
from aiogram.filters import Command
from services.news_parser import parse_drom_honda
from database.db import save_publication, get_latest_publications

router = Router()

@router.message(Command("drom"))
async def cmd_drom(message: types.Message):
    """Обработчик команды /drom - парсинг новостей Honda на Drom.ru"""
    await message.answer("🚗 Парсю новости Honda на Drom.ru...")
    
    try:
        # Парсим сайт
        raw_news = await parse_drom_honda("https://news.drom.ru/honda/")
        
        if not raw_news:
            # Если парсер не нашёл ничего на сайте
            latest = await get_latest_publications(limit=5, source="https://news.drom.ru/honda/")
            
            if not latest:
                await message.answer(
                    "❌ Не удалось найти новости на сайте.\n"
                    "📭 В базе данных пока нет сохранённых публикаций."
                )
                return
            
            result_text = "📋 <b>Последние сохранённые публикации Drom (Honda):</b>\n\n"
            for pub in latest:
                status_icon = "✅" if pub['status'] == 'text_fetched' else "🆕"
                result_text += f"{status_icon} [<b>ID: {pub['id']}</b>] {pub['title']}\n🔗 {pub['url']}\n\n"
            
            await message.answer(
                result_text,
                parse_mode="HTML",
                disable_web_page_preview=True
            )
            return
        
        # Сохраняем в БД и считаем только НОВЫЕ записи
        new_publications = []
        
        for item in raw_news:
            pub_id = await save_publication(item['title'], item['url'], item['source'])
            if pub_id:  # Только если это НОВАЯ запись
                new_publications.append({
                    'id': pub_id,
                    'title': item['title'],
                    'url': item['url']
                })
        
        if not new_publications:
            # Все найденные публикации уже есть в БД
            await message.answer("✅ Все найденные новости уже в базе данных. Новых публикаций нет.")
            return
        
        # Формируем ответ только из НОВЫХ публикаций
        result_text = f"🚙 <b>Новые новости Honda на Drom.ru ({len(new_publications)} шт.):</b>\n\n"
        
        for pub in new_publications:
            result_text += f"[<b>ID: {pub['id']}</b>] {pub['title']}\n🔗 {pub['url']}\n\n"
        
        await message.answer(
            result_text, 
            parse_mode="HTML", 
            disable_web_page_preview=True
        )
        
    except Exception as e:
        await message.answer(f"❌ Ошибка при парсинге Drom: {str(e)}")