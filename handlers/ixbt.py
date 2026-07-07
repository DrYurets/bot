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
        # Получаем новости со страницы iXBT/car/
        raw_news = await parse_ixbt_car("https://www.ixbt.com/car/")
        
        if not raw_news:
            # Если новых нет, показываем последние 5 из БД
            latest = await get_latest_publications(limit=5, source="https://www.ixbt.com/car/")
            
            if not latest:
                await message.answer(
                    "❌ Новых публикаций не найдено.\n"
                    "📭 В базе данных пока нет сохранённых публикаций."
                )
                return
            
            result_text = "📋 <b>Последние 5 публикаций (новых нет):</b>\n\n"
            for pub in latest:
                status_icon = "✅" if pub['status'] == 'text_fetched' else "🆕"
                result_text += f"{status_icon} [<b>ID: {pub['id']}</b>] {pub['title']}\n🔗 {pub['url']}\n\n"
            
            await message.answer(
                result_text,
                parse_mode="HTML",
                disable_web_page_preview=True
            )
            return
        
        # Сохраняем в БД и формируем ответ
        result_text = "🚗 <b>Автомобильные новости iXBT:</b>\n\n"
        
        for item in raw_news:
            pub_id = await save_publication(item['title'], item['url'], item['source'])
            result_text += f"[<b>ID: {pub_id}</b>] {item['title']}\n🔗 {item['url']}\n\n"
        
        await message.answer(
            result_text, 
            parse_mode="HTML", 
            disable_web_page_preview=True
        )
        
    except Exception as e:
        await message.answer(f"❌ Ошибка при парсинге iXBT: {str(e)}")