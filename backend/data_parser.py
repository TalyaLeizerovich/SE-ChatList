from datetime import date, datetime, timedelta, time
import re

WEEKDAY_MAP = {
    "monday": 0,
    "mon": 0,
    "tuesday": 1,
    "tue": 1,
    "tues": 1,
    "wednesday": 2,
    "wed": 2,
    "thursday": 3,
    "thu": 3,
    "thur": 3,
    "thurs": 3,
    "friday": 4,
    "fri": 4,
    "saturday": 5,
    "sat": 5,
    "sunday": 6,
    "sun": 6
}

DEFAULT_TIME = time(hour=9, minute=0)


def resolve_task_date(text: str) -> datetime:
    """
    Resolve task date from English text.
    
    Handles:
    - "today"
    - "tomorrow" / "tmr" / "tmrw"
    - Day names: "monday", "tuesday", etc. (full and abbreviated)
    - Full dates: DD/MM/YYYY, MM/DD/YYYY, YYYY-MM-DD
    - Time: HH:MM (optional, 12h or 24h format)
    
    Returns datetime object with date + time (default 9:00 if no time specified)
    """
    text = text.lower()
    today = date.today()

    # Extract time if present (default to 9:00)
    task_time = _extract_time(text) or DEFAULT_TIME

    # Check for full date format
    full_date = _extract_full_date(text)
    if full_date:
        return datetime.combine(full_date, task_time)

    # Check for "today"
    if "today" in text:
        return datetime.combine(today, task_time)

    # Check for "tomorrow" / "tmr" / "tmrw"
    if any(word in text for word in ["tomorrow", "tmr", "tmrw"]):
        return datetime.combine(today + timedelta(days=1), task_time)

    # Check for day names (monday, tuesday, etc.)
    for day_name, weekday_num in WEEKDAY_MAP.items():
        if day_name in text:
            next_day = _next_weekday(today, weekday_num)
            return datetime.combine(next_day, task_time)

    # Default: if no date indicator found, use today
    return datetime.combine(today, task_time)


def _extract_time(text: str):
    """
    Extract time in format HH:MM from text.
    Supports both 24h (14:30) and 12h format (2:30pm).
    Returns time object or None.
    """
    # Try 12-hour format first (e.g., "2:30pm", "2pm", "2:30 pm")
    match_12h = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)', text, re.IGNORECASE)
    if match_12h:
        hour = int(match_12h.group(1))
        minute = int(match_12h.group(2)) if match_12h.group(2) else 0
        period = match_12h.group(3).lower()
        
        # Convert to 24-hour format
        if period == "pm" and hour != 12:
            hour += 12
        elif period == "am" and hour == 12:
            hour = 0
        
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return time(hour, minute)
    
    # Try 24-hour format (e.g., "14:30")
    match_24h = re.search(r'(\d{1,2}):(\d{2})', text)
    if match_24h:
        hour, minute = map(int, match_24h.groups())
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return time(hour, minute)
    
    return None


def _extract_full_date(text: str):
    """
    Extract full date in various formats:
    - DD/MM/YYYY or DD/MM
    - MM-DD-YYYY or MM-DD
    - YYYY-MM-DD (ISO format)
    
    Returns date object or None.
    """
    # Try ISO format first (YYYY-MM-DD)
    match_iso = re.search(r'(\d{4})-(\d{1,2})-(\d{1,2})', text)
    if match_iso:
        year, month, day = map(int, match_iso.groups())
        try:
            return date(year, month, day)
        except ValueError:
            pass
    
    # Try DD/MM/YYYY or DD/MM or MM/DD/YYYY or MM/DD
    match_slash = re.search(r'(\d{1,2})/(\d{1,2})(?:/(\d{4}))?', text)
    if match_slash:
        first, second, year = match_slash.groups()
        first, second = int(first), int(second)
        year = int(year) if year else date.today().year
        
        # Try DD/MM format (common in Europe/Israel)
        try:
            return date(year, second, first)
        except ValueError:
            pass
        
        # Try MM/DD format (common in US)
        try:
            return date(year, first, second)
        except ValueError:
            pass
    
    # Try DD-MM-YYYY or DD-MM
    match_dash = re.search(r'(\d{1,2})-(\d{1,2})(?:-(\d{4}))?', text)
    if match_dash:
        day, month, year = match_dash.groups()
        day, month = int(day), int(month)
        year = int(year) if year else date.today().year
        
        try:
            return date(year, month, day)
        except ValueError:
            pass
    
    return None


def _next_weekday(start_date, target_weekday):
    """
    Get the next occurrence of a specific weekday.
    
    Args:
        start_date: Starting date
        target_weekday: 0=Monday, 1=Tuesday, ..., 6=Sunday
    
    Returns:
        date object of the next occurrence
    """
    days_ahead = target_weekday - start_date.weekday()
    if days_ahead <= 0:  # Target day already passed this week
        days_ahead += 7
    return start_date + timedelta(days=days_ahead)