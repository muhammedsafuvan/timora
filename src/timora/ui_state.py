"""UI state helpers for Timora dashboard."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Deque, Iterable

from timora.ui_helpers import format_announcement_line


@dataclass(frozen=True)
class AnnouncementEntry:
    timestamp: datetime
    speech_ok: bool


class AnnouncementHistory:
    def __init__(self, limit: int = 5) -> None:
        self._limit = max(1, limit)
        self._items: Deque[AnnouncementEntry] = deque(maxlen=self._limit)

    def add(self, timestamp: datetime, speech_ok: bool) -> None:
        self._items.appendleft(AnnouncementEntry(timestamp=timestamp, speech_ok=speech_ok))

    def lines(self) -> Iterable[str]:
        for entry in self._items:
            yield format_announcement_line(entry.timestamp, entry.speech_ok)

    def __len__(self) -> int:
        return len(self._items)
