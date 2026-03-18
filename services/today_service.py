from collections import defaultdict

from db import queries
from utils.time_utils import today_range_utc, format_duration


async def get_today_time_for_node(user_id: int, node_id: int,
                                   user_tz: str = "UTC") -> int:
    """Total finished-session time (seconds) for a node today."""
    start, end = today_range_utc(user_tz)
    return await queries.get_today_duration_for_node(user_id, node_id, start, end)


async def get_today_summary(user_id: int, user_tz: str = "UTC") -> str:
    start, end = today_range_utc(user_tz)
    sessions = await queries.get_finished_sessions_in_range(user_id, start, end)

    if not sessions:
        return "No finished sessions today."

    node_times: dict[str, int] = defaultdict(int)
    node_counts: dict[str, int] = defaultdict(int)
    total = 0

    for s in sessions:
        time = s["duration_seconds"] or 0
        node_times[s["node_name"]] += time
        node_counts[s["node_name"]] += 1
        total += time

    header = f"📊 Today — {format_duration(total)} total\n"
    lines = []
    for name, time in node_times.items():
        count = node_counts[name]
        sessions_label = f" ({count} sessions)" if count > 1 else ""
        lines.append(f"  • {name}: {format_duration(time)}{sessions_label}")

    return header + "\n".join(lines)
