"""Interval parsing utilities."""

from __future__ import annotations

import re


_INTERVAL_RE = re.compile(r"^(\d+)([smhSMH]?)$")


def parse_interval(value: str) -> int:
    """Parse an interval string into seconds.

    Accepted formats: 30s, 15m, 1h, 2h. A plain integer is treated as minutes.
    """
    if value is None:
        raise ValueError("Interval is required.")

    text = value.strip()
    if not text:
        raise ValueError("Interval is required.")

    match = _INTERVAL_RE.fullmatch(text)
    if not match:
        raise ValueError("Interval must be like 30s, 15m, 1h, or 30.")

    amount = int(match.group(1))
    if amount <= 0:
        raise ValueError("Interval must be greater than zero.")

    unit = match.group(2).lower() if match.group(2) else "m"
    multiplier = {"s": 1, "m": 60, "h": 3600}.get(unit)
    if multiplier is None:
        raise ValueError("Interval unit must be s, m, or h.")

    return amount * multiplier


def format_interval(seconds: int) -> str:
    """Return a human-readable interval label."""
    if seconds <= 0:
        raise ValueError("Interval must be greater than zero.")

    if seconds % 3600 == 0:
        hours = seconds // 3600
        unit = "hour" if hours == 1 else "hours"
        return f"{hours} {unit}"

    if seconds % 60 == 0:
        minutes = seconds // 60
        unit = "minute" if minutes == 1 else "minutes"
        return f"{minutes} {unit}"

    unit = "second" if seconds == 1 else "seconds"
    return f"{seconds} {unit}"
