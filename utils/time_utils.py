from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def now_iso() -> str:
    return now_utc().strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(s: str) -> datetime:
    s = s.replace("Z", "+00:00")
    return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)


def format_duration(seconds: int) -> str:
    if seconds < 0:
        seconds = 0
    h, remainder = divmod(seconds, 3600)
    m, s = divmod(remainder, 60)
    if h > 0:
        return f"{h}h {m:02d}m {s:02d}s"
    if m > 0:
        return f"{m}m {s:02d}s"
    return f"{s}s"


def format_local_time(iso_str: str, user_tz: str = "UTC") -> str:
    """Return HH:MM in the user's local timezone."""
    tz = ZoneInfo(user_tz)
    return parse_iso(iso_str).astimezone(tz).strftime("%H:%M")


def today_range_utc(user_tz: str = "UTC") -> tuple[str, str]:
    tz = ZoneInfo(user_tz)
    local_now = datetime.now(tz)
    start_of_day_local = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day_local = start_of_day_local + timedelta(days=1)
    start_utc = start_of_day_local.astimezone(timezone.utc)
    end_utc = end_of_day_local.astimezone(timezone.utc)
    return (
        start_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        end_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
