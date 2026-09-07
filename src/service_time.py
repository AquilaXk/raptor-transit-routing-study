"""Service-day seconds, with no modulo-24 shortcut. Seoul is the lab timezone."""
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo
import re
from .timetable import RoutingError, integer

def parse_time(value: str) -> int:
    if not isinstance(value, str) or not re.fullmatch(r"\d{1,3}:[0-5]\d:[0-5]\d", value):
        raise RoutingError("INVALID_TIME", "use H:MM:SS or HH:MM:SS; hours may exceed 23")
    hours, minutes, seconds = map(int, value.split(":"))
    return hours * 3600 + minutes * 60 + seconds

def format_time(seconds: int) -> str:
    integer(seconds, "service seconds")
    return f"{seconds // 3600:02d}:{seconds // 60 % 60:02d}:{seconds % 60:02d}"

def service_instant(service_date: date, seconds: int) -> datetime:
    """An Asia/Seoul teaching conversion, not a global GTFS/DST implementation."""
    integer(seconds, "service seconds")
    if type(service_date) is not date:
        raise RoutingError("INVALID_TIME", "a date, not a datetime, is required")
    return datetime.combine(service_date, time(), ZoneInfo("Asia/Seoul")) + timedelta(seconds=seconds)

def service_active(day: date, start: date, end: date, weekdays: frozenset[int],
                   exceptions: dict[date, bool] | None = None) -> bool:
    if start > end or any(type(n) is not int or n not in range(7) for n in weekdays):
        raise RoutingError("INVALID_CALENDAR", "invalid interval or weekday")
    if exceptions and day in exceptions:
        if type(exceptions[day]) is not bool:
            raise RoutingError("INVALID_CALENDAR", "exception must be explicit add/remove")
        return exceptions[day]
    return start <= day <= end and day.weekday() in weekdays
