"""Helper utilities for the Timora dashboard."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable

from timora.notifier import format_timestamp

@dataclass(frozen=True)
class TimezoneInfo:
    label: str
    abbreviation: str | None
    offset: str | None

    def render(self) -> str:
        parts = [self.label]
        if self.abbreviation:
            parts.append(self.abbreviation)
        if self.offset:
            parts.append(self.offset)
        return " \u00b7 ".join(parts)


def format_clock(now: datetime) -> str:
    return now.strftime("%I:%M:%S %p")


def format_date(now: datetime) -> str:
    return f"{now.strftime('%A')}, {now.strftime('%B')} {now.day:02d}, {now.year}"


def timezone_info(now: datetime) -> TimezoneInfo:
    local_now = now.astimezone()
    tzinfo = local_now.tzinfo
    key = getattr(tzinfo, "key", None)
    label = key or "Local time"
    abbreviation = local_now.tzname() or None
    offset = local_now.utcoffset()
    offset_label = None
    if offset is not None:
        total_minutes = int(offset.total_seconds() // 60)
        sign = "+" if total_minutes >= 0 else "-"
        total_minutes = abs(total_minutes)
        hours, minutes = divmod(total_minutes, 60)
        offset_label = f"UTC{sign}{hours:02d}:{minutes:02d}"
    return TimezoneInfo(label=label, abbreviation=abbreviation, offset=offset_label)


def format_countdown(seconds: float) -> str:
    remaining = max(0, int(seconds))
    if remaining == 0:
        return "Now"
    if remaining < 60:
        unit = "second" if remaining == 1 else "seconds"
        return f"In {remaining} {unit}"
    if remaining < 3600:
        minutes = remaining // 60
        unit = "minute" if minutes == 1 else "minutes"
        return f"In {minutes} {unit}"
    hours, remainder = divmod(remaining, 3600)
    minutes = remainder // 60
    hour_unit = "hour" if hours == 1 else "hours"
    if minutes:
        minute_unit = "minute" if minutes == 1 else "minutes"
        return f"In {hours} {hour_unit} {minutes} {minute_unit}"
    return f"In {hours} {hour_unit}"


def format_countdown_short(seconds: float) -> str:
    remaining = max(0, int(seconds))
    if remaining == 0:
        return "now"
    if remaining < 60:
        unit = "second" if remaining == 1 else "seconds"
        return f"in {remaining} {unit}"
    if remaining < 3600:
        minutes = remaining // 60
        unit = "minute" if minutes == 1 else "minutes"
        return f"in {minutes} {unit}"
    hours, remainder = divmod(remaining, 3600)
    minutes = remainder // 60
    hour_unit = "hour" if hours == 1 else "hours"
    if minutes:
        minute_unit = "minute" if minutes == 1 else "minutes"
        return f"in {hours} {hour_unit} {minutes} {minute_unit}"
    return f"in {hours} {hour_unit}"


def format_countdown_clock(seconds: float) -> str:
    remaining = max(0, int(seconds))
    hours, remainder = divmod(remaining, 3600)
    minutes, seconds_part = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds_part:02d}"


def progress_fraction(remaining: float, interval: int) -> float:
    if interval <= 0:
        return 0.0
    elapsed = max(0.0, interval - max(0.0, remaining))
    fraction = elapsed / interval
    return min(1.0, max(0.0, fraction))


def format_next_time(next_time: datetime) -> str:
    return next_time.strftime("%I:%M %p")


def render_announcements(lines: Iterable[str]) -> str:
    rendered = list(lines)
    if not rendered:
        return "No announcements yet."
    return "\n".join(rendered)


def format_announcement_line(timestamp: datetime, speech_ok: bool) -> str:
    return format_timestamp(timestamp)


def estimate_next_from_interval(now: datetime, remaining_seconds: float) -> datetime:
    return now + timedelta(seconds=max(0.0, remaining_seconds))
