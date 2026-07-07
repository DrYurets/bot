from aiogram import Router, types, F
from aiogram.filters import Command
from services.image_processor import process_image
from aiogram.types import FSInputFile
from pathlib import Path
import tempfile

router = Router()

@router.message(Command("images"))
async def cmd_images_start(message: types.Message):
    """Обработчик команды /images - начало"""
    await message.answer(
        "📸 Отправьте мне изображение или несколько изображений.\n"
        "Я уменьшу их до нужного размера."
    )

@router.message(F.photo)
async def handle_photo(message: types.Message):
    """Обработчик получения фото"""
    # Получаем самое большое фото из сообщения
    photo = message.photo[-1]
    
    await message.answer("⏳ Обрабатываю изображение...")
    
    try:
        # Скачиваем фото
        file = await message.bot.get_file(photo.file_id)
        file_bytes = await message.bot.download_file(file.file_path)
        image_bytes = file_bytes.read()
        
        # Обрабатываем изображение
        processed_bytes = await process_image(image_bytes)
        
        # Сохраняем во временный файл
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            temp_file.write(processed_bytes)
            temp_path = temp_file.name
        
        # Отправляем обработанное изображение
        processed_photo = FSInputFile(temp_path)
        await message.answer_photo(processed_photo, caption="✅ Обработанное изображение")
        
        # Удаляем временный файл
        Path(temp_path).unlink()
        
    except Exception as e:
        await message.answer(f"❌ Ошибка при обработке изображения: {str(e)}")

@router.message(F.document)
async def handle_document(message: types.Message):
    """Обработчик получения документа (изображения как файл)"""
    document = message.document
    
    # Проверяем, что это изображение
    if not document.mime_type.startswith('image/'):
        await message.answer("⚠️ Пожалуйста, отправьте изображение.")
        return
    
    await message.answer("⏳ Обрабатываю изображение...")
    
    try:
        # Скачиваем документ
        file = await message.bot.get_file(document.file_id)
        file_bytes = await message.bot.download_file(file.file_path)
        image_bytes = file_bytes.read()
        
        # Обрабатываем изображение
        processed_bytes = await process_image(image_bytes)
        
        # Сохраняем во временный файл
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            temp_file.write(processed_bytes)
            temp_path = temp_file.name
        
        # Отправляем как документ
        processed_doc = FSInputFile(temp_path, filename=f"processed_{document.file_name}")
        await message.answer_document(processed_doc, caption="✅ Обработанное изображение")
        
        # Удаляем временный файл
        Path(temp_path).unlink()
        
    except Exception as e:
        await message.answer(f"❌ Ошибка при обработке изображения: {str(e)}")