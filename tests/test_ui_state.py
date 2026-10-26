from datetime import datetime

from timora.ui_state import AnnouncementHistory


def test_announcement_history_ordering() -> None:
    history = AnnouncementHistory(limit=3)
    history.add(datetime(2026, 10, 25, 9, 0), True)
    history.add(datetime(2026, 10, 25, 9, 1), False)
    lines = list(history.lines())
    assert lines[0].startswith("9:01")
    assert len(lines) == 2


def test_announcement_history_limit() -> None:
    history = AnnouncementHistory(limit=2)
    history.add(datetime(2026, 10, 25, 9, 0), True)
    history.add(datetime(2026, 10, 25, 9, 1), True)
    history.add(datetime(2026, 10, 25, 9, 2), True)
    assert len(list(history.lines())) == 2
