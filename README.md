# Telegram Bot

Многофункциональный Telegram бот для работы с новостями, изображениями и текстом.

## Возможности

- `/news` - парсит источники новостей и показывает новые публикации с ID
- `/processing` - извлекает полный текст публикаций по их ID
- `/images` - уменьшает размер изображений
- `/text` - команда для работы с текстом (будет реализована)

## Установка

### Требования
- Python 3.10+
- pip

### Шаги установки

1. Клонируйте репозиторий или скопируйте файлы проекта

2. Создайте виртуальное окружение:
```bash
python -m venv venv

# Для Windows:
venv\Scripts\activate

# Для Linux/Mac:
source venv/bin/activate
```
3. Установите библиотеки командой:
    - `pip install aiogram aiohttp aiosqlite python-dotenv pydantic-settings beautifulsoup4 lxml feedparser Pillow trafilatura`
