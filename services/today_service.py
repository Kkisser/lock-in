from db import queries
from services.session_service import calc_elapsed
from utils.time_utils import today_range_utc, format_duration


async def get_today_summary(user_id: int, user_tz: str = "UTC") -> str:
    start, end = today_range_utc(user_tz)
    sessions = await queries.get_finished_sessions_in_range(user_id, start, end)

    if not sessions:
        return "No finished sessions today."

    total = 0
    lines = []
    for s in sessions:
        elapsed = await calc_elapsed(s["id"])
        total += elapsed
        lines.append(f"  • {s['event_name']}: {format_duration(elapsed)}")

    header = f"📊 Today — {format_duration(total)} total\n"
    return header + "\n".join(lines)
