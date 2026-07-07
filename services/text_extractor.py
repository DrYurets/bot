import aiohttp
import trafilatura
from typing import Optional

async def extract_text_from_url(url: str) -> str:
    """Скачивает страницу и извлекает чистый текст"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as response:
            response.raise_for_status()
            html = await response.text()
    
    # Извлекаем основной текст страницы
    extracted_text = trafilatura.extract(
        html,
        include_comments=False,
        include_tables=True,
        favor_precision=True,
        include_images=False,
        include_links=False
    )
    
    if not extracted_text:
        raise ValueError("Не удалось извлечь текст из страницы")
    
    return extracted_text.strip()