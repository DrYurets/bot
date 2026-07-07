from aiogram import Router, types
from aiogram.filters import Command
from services.news_parser import parse_ixbt_car
from database.db import save_publication, get_latest_publications

router = Router()

@router.message(Command("ixbt"))
async def cmd_ixbt(message: types.Message):
    """Обработчик команды /ixbt - парсинг автомобильных новостей iXBT"""
    await message.answer("⏳ Парсю автомобильные новости iXBT...")
    
    try:
        # Парсим сайт
        raw_news = await parse_ixbt_car("https://www.ixbt.com/car/")
        
        if not raw_news:
            # Если парсер не нашёл ничего на сайте
            latest = await get_latest_publications(limit=5, source="https://www.ixbt.com/car/")
            
            if not latest:
                await message.answer(
                    "❌ Не удалось найти новости на сайте.\n"
                    "📭 В базе данных пока нет сохранённых публикаций."
                )
                return
            
            result_text = "📋 <b>Последние сохранённые публикации (сайт недоступен):</b>\n\n"
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
        result_text = f"🚗 <b>Новые автомобильные новости iXBT ({len(new_publications)} шт.):</b>\n\n"
        
        for pub in new_publications:
            result_text += f"[<b>ID: {pub['id']}</b>] {pub['title']}\n🔗 {pub['url']}\n\n"
        
        await message.answer(
            result_text, 
            parse_mode="HTML", 
            disable_web_page_preview=True
        )
        
    except Exception as e:
        await message.answer(f"❌ Ошибка при парсинге iXBT: {str(e)}")