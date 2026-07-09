from datetime import datetime

DISPLAY_FORMAT = "%d.%m.%Y %H:%M"
DATE_ONLY_FORMAT = "%d.%m.%Y"

def format_publication_datetime(value: str | None) -> str:
    """Форматирует ISO pubdatetime в ДД.ММ.ГГГГ чч:мм (или только дату, если время отсутствует)."""
    if not value:
        return "—"

    try:
        dt = datetime.fromisoformat(value)
        if dt.hour == 0 and dt.minute == 0 and "T" not in value:
            return dt.strftime(DATE_ONLY_FORMAT)
        return dt.strftime(DISPLAY_FORMAT)
    except (ValueError, TypeError):
        return "—"

def drom_date_to_iso(date_str: str | None) -> str | None:
    """Конвертирует дату Drom (ДД.ММ.ГГГГ) в ISO для хранения в БД."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str.strip(), "%d.%m.%Y").date().isoformat()
    except ValueError:
        return None

def publication_sort_key(pub: dict) -> tuple:
    """Ключ сортировки: новые публикации сверху."""
    return (pub.get("published_at") or "", pub.get("created_at") or "")
