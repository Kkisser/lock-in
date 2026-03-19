from datetime import datetime, timezone

from db import queries
from utils.time_utils import today_range_utc, now_iso, parse_iso, format_duration


async def create_item(user_id: int, action_id: int, tracking_type: str,
                      counter_target: int | None, counter_unit: str | None,
                      timer_target_seconds: int | None) -> int:
    """Create a longterm item and start its first run."""
    lt_id = await queries.create_longterm_item(
        user_id, action_id, tracking_type,
        counter_target, counter_unit, timer_target_seconds,
    )
    await queries.create_run(lt_id)
    return lt_id


async def get_today_progress(lt: dict, user_tz: str) -> dict:
    """Return today's counter and/or timer progress for a longterm item."""
    start, end = today_range_utc(user_tz)
    result = {}
    if lt["tracking_type"] in ("counter", "both"):
        result["counter_done"] = await queries.get_today_counter_total(lt["id"], start, end)
    if lt["tracking_type"] in ("timer", "both"):
        result["timer_done"] = await queries.get_today_duration_for_action(
            lt["user_id"], lt["action_id"], start, end
        )
    return result


async def add_counter(lt_id: int, user_id: int, amount: int, user_tz: str):
    recorded_at = now_iso()
    await queries.add_counter_entry(lt_id, user_id, amount, recorded_at)


def format_progress(lt: dict, progress: dict) -> str:
    """Build compact progress string, e.g. '✅ 3/3 times | ⏳ 15/20 min'"""
    parts = []
    if lt["tracking_type"] in ("counter", "both"):
        done = progress.get("counter_done", 0)
        target = lt["counter_target"]
        unit = lt["counter_unit"] or "times"
        if target:
            icon = "✅" if done >= target else "⏳"
            parts.append(f"{icon} {done}/{target} {unit}")
        else:
            parts.append(f"🔢 {done} {unit}")
    if lt["tracking_type"] in ("timer", "both"):
        done_s = progress.get("timer_done", 0)
        target_s = lt["timer_target_seconds"]
        done_min = done_s // 60
        if target_s:
            target_min = target_s // 60
            icon = "✅" if done_s >= target_s else "⏳"
            parts.append(f"{icon} {done_min}/{target_min} min")
        else:
            parts.append(f"⏱ {done_min} min")
    return " | ".join(parts)


async def get_run_day(lt_id: int) -> int:
    """Number of days since current run started (1-based), or 0 if no run."""
    run = await queries.get_active_run(lt_id)
    if not run:
        return 0
    started = parse_iso(run["started_at"])
    now = datetime.now(timezone.utc)
    return (now - started).days + 1


async def end_and_reset_run(lt_id: int):
    """End the current run (manual) and start a new one."""
    run = await queries.get_active_run(lt_id)
    if run:
        await queries.end_run(run["id"], "manual")
    await queries.create_run(lt_id)


async def delete_item(lt_id: int):
    await queries.delete_longterm_item(lt_id)
