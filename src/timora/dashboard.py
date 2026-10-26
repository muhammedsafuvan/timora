"""Textual dashboard for Timora."""

from __future__ import annotations

import threading
import time
from datetime import datetime, timedelta

from rich.text import Text

from timora.interval import format_interval
from timora.notifier import VoiceNotifier
from timora.scheduler import ClockSchedule, IntervalSchedule, run_schedule
from timora.ui_helpers import (
    format_countdown_clock,
    format_countdown_short,
    format_date,
    format_next_time,
    progress_fraction,
    render_announcements,
    timezone_info,
)
from timora.ui_state import AnnouncementHistory

try:
    from textual.app import App, ComposeResult
    from textual.containers import Horizontal, Vertical
    from textual.events import Resize
    from textual.reactive import reactive
    from textual.widgets import Static
except Exception as exc:  # pragma: no cover - handled by CLI fallback
    App = None  # type: ignore[assignment]
    ComposeResult = None  # type: ignore[assignment]
    Horizontal = None  # type: ignore[assignment]
    Vertical = None  # type: ignore[assignment]
    Static = None  # type: ignore[assignment]
    Resize = None  # type: ignore[assignment]
    reactive = lambda value=None: value  # type: ignore[assignment]
    _TEXTUAL_IMPORT_ERROR = exc
else:
    _TEXTUAL_IMPORT_ERROR = None


_BLOCK_GLYPHS = {
    "0": ["███", "█ █", "█ █", "█ █", "███"],
    "1": [" █ ", "██ ", " █ ", " █ ", "███"],
    "2": ["███", "  █", "███", "█  ", "███"],
    "3": ["███", "  █", "███", "  █", "███"],
    "4": ["█ █", "█ █", "███", "  █", "  █"],
    "5": ["███", "█  ", "███", "  █", "███"],
    "6": ["███", "█  ", "███", "█ █", "███"],
    "7": ["███", "  █", "  █", "  █", "  █"],
    "8": ["███", "█ █", "███", "█ █", "███"],
    "9": ["███", "█ █", "███", "  █", "███"],
    ":": [" ", "█", " ", "█", " "],
}


class TimoraDashboard(App):
    CSS_PATH = "timora.tcss"
    BINDINGS = [("q", "quit", "Quit"), ("p", "toggle_pause", "Pause/Resume")]

    is_paused = reactive(False)
    clock_text = reactive(Text(""))
    date_text = reactive("")
    timezone_text = reactive("")
    next_time_text = reactive("")
    countdown_text = reactive("")
    interval_text = reactive("")
    mode_text = reactive("")
    progress_label = reactive("")
    progress_percent = reactive(0)
    progress_bar = reactive(Text(""))
    announcements_text = reactive("")

    def __init__(
        self,
        *,
        interval_seconds: int,
        mode: str,
        notifier: VoiceNotifier,
    ) -> None:
        super().__init__()
        self._interval_seconds = interval_seconds
        self._mode = mode
        self._notifier = notifier
        self._history = AnnouncementHistory(limit=5)
        self._stop_event = threading.Event()
        self._scheduler_thread: threading.Thread | None = None
        self._schedule = self._create_schedule()
        self._paused_remaining: float | None = None
        self._paused_at_mono: float | None = None

    def _create_schedule(self) -> IntervalSchedule | ClockSchedule:
        if self._mode == "clock":
            return ClockSchedule.start(self._interval_seconds, datetime.now)
        return IntervalSchedule.start(self._interval_seconds, time.monotonic)

    def compose(self) -> ComposeResult:
        with Vertical(id="root"):
            with Vertical(id="content"):
                with Horizontal(id="header"):
                    yield Static("TIMORA", id="title")
                    yield Static("● ACTIVE", id="status")
                with Vertical(id="clock-block"):
                    yield Static("", id="clock")
                with Vertical(id="date-block"):
                    yield Static("", id="date")
                    yield Static("", id="timezone")
                with Horizontal(id="cards"):
                    with Vertical(classes="panel"):
                        yield Static("NEXT REMINDER", classes="section-title")
                        yield Static("--:-- --", id="next-time", classes="card-value")
                        yield Static("in -- minutes", id="countdown", classes="card-subtitle")
                    with Vertical(classes="panel"):
                        yield Static("INTERVAL", classes="section-title")
                        yield Static("", id="interval", classes="card-value")
                        yield Static("", id="mode", classes="card-subtitle")
                with Vertical(id="progress-block"):
                    with Horizontal(id="progress-meta"):
                        yield Static("NEXT REMINDER IN 00:00:00", id="progress-remaining")
                        yield Static("0%", id="progress-percent")
                    yield Static("", id="progress-bar")
                with Vertical(id="announcements-block"):
                    yield Static("RECENT ANNOUNCEMENTS", id="announcements-title")
                    yield Static("No announcements yet.", id="announcements")
            yield Static("Press q to quit, p to pause/resume", id="footer")

    def on_mount(self) -> None:
        self.set_interval(1.0, self._tick)
        self._start_scheduler()
        interval_label = format_interval(self._interval_seconds)
        self.interval_text = interval_label
        self.mode_text = f"{self._mode} mode"

    def on_unmount(self) -> None:
        self._stop_event.set()
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=1.0)

    def _start_scheduler(self) -> None:
        self._scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self._scheduler_thread.start()

    def _run_scheduler(self) -> None:
        def on_fire(timestamp: datetime, speech_ok: bool) -> None:
            self.call_from_thread(self._record_fire, timestamp, speech_ok)

        run_schedule(
            mode=self._mode,
            interval_seconds=self._interval_seconds,
            notifier=self._notifier,
            out=lambda _: None,
            on_fire=on_fire,
            schedule=self._schedule,
            stop_event=self._stop_event,
        )

    def _record_fire(self, timestamp: datetime, speech_ok: bool) -> None:
        self._history.add(timestamp, speech_ok)
        self._update_announcements()

    def _update_announcements(self) -> None:
        self.announcements_text = render_announcements(self._history.lines())

    def action_toggle_pause(self) -> None:
        if self.is_paused:
            self.is_paused = False
            self._resume_scheduler()
        else:
            self._pause_scheduler()
            self.is_paused = True

    def _pause_scheduler(self) -> None:
        now = datetime.now().astimezone()
        if self._mode == "clock":
            remaining = (self._schedule.next_fire - now).total_seconds()
        else:
            remaining = self._schedule.remaining(time.monotonic())
        self._paused_remaining = max(0.0, remaining)
        self._paused_at_mono = time.monotonic()
        self._stop_event.set()
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=1.0)

    def _resume_scheduler(self) -> None:
        remaining = self._paused_remaining
        paused_at = self._paused_at_mono
        self._paused_remaining = None
        self._paused_at_mono = None
        self._stop_event.clear()
        if remaining is None:
            self._schedule = self._create_schedule()
        elif self._mode == "clock":
            now = datetime.now().astimezone()
            elapsed = 0.0
            if paused_at is not None:
                elapsed = max(0.0, time.monotonic() - paused_at)
            remaining = remaining - elapsed
            if remaining <= 0:
                self._schedule = ClockSchedule.start(self._interval_seconds, datetime.now)
            else:
                self._schedule = ClockSchedule(
                    interval_seconds=self._interval_seconds,
                    next_fire=now + timedelta(seconds=remaining),
                )
        else:
            now_mono = time.monotonic()
            elapsed = 0.0
            if paused_at is not None:
                elapsed = max(0.0, now_mono - paused_at)
            remaining = remaining - elapsed
            if remaining <= 0:
                remaining = float(self._interval_seconds)
            self._schedule = IntervalSchedule(
                interval_seconds=self._interval_seconds,
                next_fire_mono=now_mono + remaining,
            )
        self._start_scheduler()

    def on_resize(self, event: Resize) -> None:
        self.progress_bar = self._render_progress_bar(self.progress_percent)

    def watch_is_paused(self, paused: bool) -> None:
        status = self.query_one("#status", Static)
        if paused:
            status.update("● PAUSED")
            status.add_class("paused")
        else:
            status.update("● ACTIVE")
            status.remove_class("paused")

    def watch_clock_text(self, value: Text) -> None:
        self.query_one("#clock", Static).update(value)

    def watch_date_text(self, value: str) -> None:
        self.query_one("#date", Static).update(value)

    def watch_timezone_text(self, value: str) -> None:
        self.query_one("#timezone", Static).update(value)

    def watch_next_time_text(self, value: str) -> None:
        self.query_one("#next-time", Static).update(value)

    def watch_countdown_text(self, value: str) -> None:
        self.query_one("#countdown", Static).update(value)

    def watch_interval_text(self, value: str) -> None:
        self.query_one("#interval", Static).update(value)

    def watch_mode_text(self, value: str) -> None:
        self.query_one("#mode", Static).update(value)

    def watch_progress_label(self, value: str) -> None:
        self.query_one("#progress-remaining", Static).update(value)

    def watch_progress_percent(self, value: int) -> None:
        self.query_one("#progress-percent", Static).update(f"{value}%")

    def watch_progress_bar(self, value: Text) -> None:
        self.query_one("#progress-bar", Static).update(value)

    def watch_announcements_text(self, value: str) -> None:
        self.query_one("#announcements", Static).update(value)

    def _render_block_time(self, now: datetime) -> Text:
        time_text = now.strftime("%I:%M:%S")
        period = now.strftime("%p")
        rows = [""] * 5
        for char in time_text:
            glyph = _BLOCK_GLYPHS.get(char)
            if glyph is None:
                continue
            expanded = ["".join(cell * 2 for cell in row) for row in glyph]
            for idx in range(5):
                if rows[idx]:
                    rows[idx] += " "
                rows[idx] += expanded[idx]

        text = Text()
        for idx, row in enumerate(rows):
            text.append(row, style="bold #ffffff")
            if idx == 4:
                text.append(f" {period}", style="bold #8fe3c4")
            if idx < 4:
                text.append("\n")
        return text

    def _render_progress_bar(self, percent: int) -> Text:
        widget = self.query_one("#progress-bar", Static)
        width = widget.size.width
        if width <= 0:
            return Text("")
        blocks = 24
        gap = 1
        usable = width - gap * (blocks - 1)
        if usable < blocks:
            usable = blocks
        base_width = max(1, usable // blocks)
        remainder = max(0, usable - base_width * blocks)
        filled_blocks = max(0, min(blocks, round(percent / 100 * blocks)))

        text = Text()
        for row in range(2):
            for idx in range(blocks):
                block_width = base_width + (1 if idx < remainder else 0)
                style = "#8fe3c4" if idx < filled_blocks else "#2b3a37"
                text.append("█" * block_width, style=style)
                if idx < blocks - 1:
                    text.append(" ")
            if row == 0:
                text.append("\n")
        return text

    def _tick(self) -> None:
        now = datetime.now().astimezone()
        self.clock_text = self._render_block_time(now)
        self.date_text = format_date(now)
        self.timezone_text = timezone_info(now).render().upper()

        if self.is_paused:
            return

        if self._mode == "clock":
            next_fire = self._schedule.next_fire
            remaining = (next_fire - now).total_seconds()
        else:
            now_mono = time.monotonic()
            remaining = self._schedule.remaining(now_mono)
            next_fire = now + timedelta(seconds=max(0.0, remaining))

        self.next_time_text = format_next_time(next_fire)
        self.countdown_text = format_countdown_short(remaining)
        progress = progress_fraction(remaining, self._interval_seconds)
        percent = int(round(progress * 100))
        self.progress_label = f"NEXT REMINDER IN {format_countdown_clock(remaining)}"
        self.progress_percent = percent
        self.progress_bar = self._render_progress_bar(percent)


def run_dashboard(
    *,
    interval_seconds: int,
    mode: str,
    notifier: VoiceNotifier,
) -> int:
    if App is None:
        raise RuntimeError(str(_TEXTUAL_IMPORT_ERROR))
    app = TimoraDashboard(interval_seconds=interval_seconds, mode=mode, notifier=notifier)
    app.run()
    return 0
