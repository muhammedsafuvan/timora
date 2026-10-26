from datetime import datetime, timezone

try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover
    ZoneInfo = None  # type: ignore[assignment]

from timora.ui_helpers import (
    format_clock,
    format_countdown,
    format_date,
    estimate_next_from_interval,
    progress_fraction,
    render_announcements,
    timezone_info,
)


def test_format_clock() -> None:
    dt = datetime(2026, 10, 25, 9, 5, 42)
    assert format_clock(dt) == "09:05:42 AM"


def test_format_date() -> None:
    dt = datetime(2026, 10, 25)
    assert format_date(dt) == "Sunday, October 25, 2026"


def test_format_countdown() -> None:
    assert format_countdown(0) == "Now"
    assert format_countdown(1) == "In 1 second"
    assert format_countdown(59) == "In 59 seconds"
    assert format_countdown(60) == "In 1 minute"
    assert format_countdown(3600) == "In 1 hour"
    assert format_countdown(3660) == "In 1 hour 1 minute"


def test_progress_fraction() -> None:
    assert progress_fraction(60, 60) == 0.0
    assert progress_fraction(30, 60) == 0.5
    assert progress_fraction(0, 60) == 1.0


def test_timezone_info_fallback() -> None:
    dt = datetime(2026, 10, 25, tzinfo=timezone.utc)
    info = timezone_info(dt)
    assert "UTC" in info.render()


def test_timezone_info_zoneinfo() -> None:
    if ZoneInfo is None:
        return
    dt = datetime(2026, 10, 25, tzinfo=ZoneInfo("UTC"))
    info = timezone_info(dt)
    assert "UTC" in info.render()


def test_render_announcements_empty() -> None:
    assert render_announcements([]) == "No announcements yet."


def test_estimate_next_from_interval() -> None:
    now = datetime(2026, 10, 25, 9, 0)
    next_time = estimate_next_from_interval(now, 90)
    assert next_time.minute == 1
