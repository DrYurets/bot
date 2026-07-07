import aiohttp
import feedparser
from typing import List, Dict
from bs4 import BeautifulSoup
import asyncio
from database.db import check_url_exists
from config import news_sources_list, max_news_per_source
from urllib.parse import urljoin, urlparse
import re

async def parse_rss_feed(feed_url: str) -> List[Dict]:
    """Парсит RSS фид"""
    print(f"[RSS] Пытаюсь загрузить: {feed_url}")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(feed_url, timeout=15) as response:
                print(f"[RSS] Статус ответа: {response.status}")
                if response.status == 200:
                    content = await response.text()
                    print(f"[RSS] Получено байт: {len(content)}")
                    feed = feedparser.parse(content)
                    print(f"[RSS] Найдено записей: {len(feed.entries)}")
                    
                    items = []
                    for entry in feed.entries[:max_news_per_source]:
                        items.append({
                            'title': entry.title,
                            'url': entry.link,
                            'source': feed_url
                        })
                    return items
    except Exception as e:
        print(f"[RSS] ❌ Ошибка при парсинге {feed_url}: {e}")
        return []
    
    return []

async def parse_drom_honda(source_url: str) -> List[Dict]:
    """Специализированный парсер для Drom.ru раздел Honda"""
    print(f"[DROM] Пытаюсь загрузить: {source_url}")
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(source_url, headers=headers, timeout=15) as response:
                print(f"[DROM] Статус ответа: {response.status}")
                if response.status == 200:
                    html = await response.text()
                    print(f"[DROM] Получено байт: {len(html)}")
                    soup = BeautifulSoup(html, 'lxml')
                    
                    items = []
                    news_links = soup.find_all('a', href=True)
                    
                    for link in news_links:
                        href = link.get('href', '')
                        title = link.get_text(strip=True)
                        
                        if '/info/' in href or '/news/' in href:
                            if len(title) >= 10 and title not in ['Читать далее', 'Подробнее', 'Все новости']:
                                if not href.startswith('http'):
                                    href = urljoin(source_url, href)
                                
                                if 'honda' in href.lower() or 'honda' in title.lower():
                                    items.append({
                                        'title': title,
                                        'url': href,
                                        'source': source_url
                                    })
                    
                    seen_urls = set()
                    unique_items = []
                    for item in items:
                        if item['url'] not in seen_urls:
                            seen_urls.add(item['url'])
                            unique_items.append(item)
                    
                    print(f"[DROM] Найдено новостей: {len(unique_items)}")
                    return unique_items[:max_news_per_source]
                    
    except Exception as e:
        print(f"[DROM] ❌ Ошибка при парсинге {source_url}: {e}")
        return []
    
    return []

async def parse_ixbt_car(source_url: str) -> List[Dict]:
    """Специализированный парсер для iXBT.com раздел Автомобили"""
    print(f"[IXBT-CAR] Пытаюсь загрузить: {source_url}")
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://www.ixbt.com/",
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(source_url, headers=headers, timeout=15) as response:
                print(f"[IXBT-CAR] Статус ответа: {response.status}")
                if response.status != 200:
                    return []
                
                html = await response.text()
                print(f"[IXBT-CAR] Получено байт: {len(html)}")
                soup = BeautifulSoup(html, 'lxml')
                
                items = []
                seen_urls = set()
                
                # Паттерн для даты: "12 июн 09:00", "06 апр 10:00" и т.д.
                date_pattern = re.compile(r'\d{1,2}\s+(янв|фев|мар|апр|май|июн|июл|авг|сен|окт|ноя|дек)\s+\d{2}:\d{2}', re.IGNORECASE)
                
                # Ищем все текстовые узлы с датами
                all_text = soup.find_all(string=True)
                
                for text_node in all_text:
                    text = str(text_node).strip()
                    
                    # Проверяем, содержит ли этот текст дату
                    if date_pattern.search(text):
                        # Нашли дату! Теперь ищем родительский контейнер новости
                        parent = text_node.parent
                        
                        # Поднимаемся на несколько уровней вверх, чтобы найти контейнер новости
                        for _ in range(5):
                            if parent is None:
                                break
                            
                            # Ищем ссылку в этом контейнере
                            link = parent.find('a', href=True)
                            
                            if link:
                                href = link.get('href', '')
                                title = link.get_text(strip=True)
                                
                                # Проверяем, что это реальная новость
                                if len(title) >= 20 and title not in ['Читать далее', 'Подробнее', 'Все новости']:
                                    # Преобразуем относительный URL в абсолютный
                                    if not href.startswith('http'):
                                        href = urljoin(source_url, href)
                                    
                                    # Проверяем, что это ссылка на iXBT
                                    if 'ixbt.com' in href:
                                        # Проверяем, что это новость (не служебная ссылка)
                                        # Новости имеют /news/ или /car/ с числом в URL
                                        if '/news/' in href or re.search(r'/car/\d+/', href):
                                            # Убираем дубликаты
                                            if href not in seen_urls:
                                                seen_urls.add(href)
                                                items.append({
                                                    'title': title,
                                                    'url': href,
                                                    'source': source_url
                                                })
                                                break
                            
                            parent = parent.parent
                
                print(f"[IXBT-CAR] Найдено реальных новостей: {len(items)}")
                
                # Выводим первые 5 найденных для отладки
                for i, item in enumerate(items[:5], 1):
                    print(f"[IXBT-CAR]   {i}. {item['title'][:60]}...")
                    print(f"[IXBT-CAR]      {item['url']}")
                
                return items[:max_news_per_source]
                    
    except Exception as e:
        print(f"[IXBT-CAR] ❌ Ошибка при парсинге {source_url}: {e}")
        return []
    
    return []

async def parse_motor_search(source_url: str) -> List[Dict]:
    """Специализированный парсер для Motor.ru поиск"""
    print(f"[MOTOR] Пытаюсь загрузить: {source_url}")
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(source_url, headers=headers, timeout=15) as response:
                print(f"[MOTOR] Статус ответа: {response.status}")
                if response.status == 200:
                    html = await response.text()
                    print(f"[MOTOR] Получено байт: {len(html)}")
                    soup = BeautifulSoup(html, 'lxml')
                    
                    items = []
                    all_links = soup.find_all('a', href=True)
                    
                    for link in all_links:
                        href = link.get('href', '')
                        title = link.get_text(strip=True)
                        
                        if '/news/' in href or '/articles/' in href or '/test-drives/' in href:
                            if len(title) >= 10 and title not in ['Читать далее', 'Подробнее']:
                                if not href.startswith('http'):
                                    href = urljoin(source_url, href)
                                
                                items.append({
                                    'title': title,
                                    'url': href,
                                    'source': source_url
                                })
                    
                    seen_urls = set()
                    unique_items = []
                    for item in items:
                        if item['url'] not in seen_urls:
                            seen_urls.add(item['url'])
                            unique_items.append(item)
                    
                    print(f"[MOTOR] Найдено новостей: {len(unique_items)}")
                    return unique_items[:max_news_per_source]
                    
    except Exception as e:
        print(f"[MOTOR] ❌ Ошибка при парсинге {source_url}: {e}")
        return []
    
    return []

async def parse_generic_html(source_url: str) -> List[Dict]:
    """Универсальный HTML парсер для других сайтов"""
    print(f"[HTML] Пытаюсь загрузить: {source_url}")
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(source_url, headers=headers, timeout=15) as response:
                print(f"[HTML] Статус ответа: {response.status}")
                if response.status == 200:
                    html = await response.text()
                    print(f"[HTML] Получено байт: {len(html)}")
                    soup = BeautifulSoup(html, 'lxml')
                    
                    items = []
                    
                    articles = soup.find_all('article')
                    for article in articles[:max_news_per_source]:
                        link = article.find('a', href=True)
                        title_elem = article.find(['h1', 'h2', 'h3', 'h4'])
                        
                        if link and title_elem:
                            href = link.get('href', '')
                            title = title_elem.get_text(strip=True)
                            
                            if len(title) >= 10:
                                if not href.startswith('http'):
                                    href = urljoin(source_url, href)
                                
                                items.append({
                                    'title': title,
                                    'url': href,
                                    'source': source_url
                                })
                    
                    if not items:
                        news_classes = ['news', 'article', 'post', 'item', 'story', 'entry']
                        for class_name in news_classes:
                            containers = soup.find_all(class_=lambda x: x and class_name in x.lower())
                            for container in containers[:max_news_per_source]:
                                link = container.find('a', href=True)
                                title_elem = container.find(['h1', 'h2', 'h3', 'h4'])
                                
                                if link and title_elem:
                                    href = link.get('href', '')
                                    title = title_elem.get_text(strip=True)
                                    
                                    if len(title) >= 10:
                                        if not href.startswith('http'):
                                            href = urljoin(source_url, href)
                                        
                                        items.append({
                                            'title': title,
                                            'url': href,
                                            'source': source_url
                                        })
                    
                    seen_urls = set()
                    unique_items = []
                    for item in items:
                        if item['url'] not in seen_urls:
                            seen_urls.add(item['url'])
                            unique_items.append(item)
                    
                    print(f"[HTML] Найдено новостей: {len(unique_items)}")
                    return unique_items[:max_news_per_source]
                    
    except Exception as e:
        print(f"[HTML] ❌ Ошибка при парсинге {source_url}: {e}")
        return []
    
    return []

async def parse_new_sources() -> List[Dict]:
    """Парсит все источники и возвращает только новые публикации"""
    print(f"\n[PARSER] === Начало парсинга ===")
    print(f"[PARSER] Источников для обработки: {len(news_sources_list)}")
    print(f"[PARSER] Лимит новостей с источника: {max_news_per_source}")
    
    if not news_sources_list:
        print("[PARSER] ⚠️ Список источников ПУСТОЙ!")
        return []
    
    all_items = []
    tasks = []
    
    for source in news_sources_list:
        source = source.strip()
        if not source:
            continue
        
        domain = urlparse(source).netloc.lower()
        
        if any(keyword in source.lower() for keyword in ['rss', 'feed', 'xml', 'atom']):
            print(f"[PARSER] Источник определён как RSS: {source}")
            tasks.append(parse_rss_feed(source))
        elif 'drom.ru' in domain:
            print(f"[PARSER] Источник определён как Drom.ru: {source}")
            tasks.append(parse_drom_honda(source))
        elif 'ixbt.com' in domain:
            print(f"[PARSER] Источник определён как iXBT.com: {source}")
            tasks.append(parse_ixbt_car(source))
        elif 'motor.ru' in domain:
            print(f"[PARSER] Источник определён как Motor.ru: {source}")
            tasks.append(parse_motor_search(source))
        else:
            print(f"[PARSER] Источник определён как HTML: {source}")
            tasks.append(parse_generic_html(source))
    
    if not tasks:
        print("[PARSER] ⚠️ Нет задач для выполнения!")
        return []
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"[PARSER] ❌ Исключение от источника {i}: {result}")
        elif isinstance(result, list):
            print(f"[PARSER] ✅ От источника {i} получено {len(result)} элементов")
            all_items.extend(result)
    
    print(f"[PARSER] Всего собрано элементов: {len(all_items)}")
    
    new_items = []
    for item in all_items:
        exists = await check_url_exists(item['url'])
        if not exists:
            new_items.append(item)
        else:
            print(f"[PARSER] Пропущено (уже в БД): {item['url'][:50]}...")
    
    print(f"[PARSER] Новых элементов: {len(new_items)}")
    print(f"[PARSER] === Конец парсинга ===\n")
    
    return new_items