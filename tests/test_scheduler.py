from datetime import datetime, timedelta
from threading import Event

from timora.notifier import VoiceNotifier
from timora.scheduler import (
    ClockSchedule,
    IntervalSchedule,
    clock_loop,
    interval_loop,
    next_clock_boundary,
    run_schedule,
)


class FakeClock:
    def __init__(self) -> None:
        self.now_value = 0.0
        self.sleeps = []

    def monotonic(self) -> float:
        return self.now_value

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now_value += seconds


class FakeNotifier(VoiceNotifier):
    def __init__(self) -> None:
        self._say_cmd = None
        self.messages = []

    def is_available(self) -> bool:
        return False

    def speak(self, message: str) -> bool:
        self.messages.append(message)
        return False


def test_interval_loop_schedules_and_stops() -> None:
    clock = FakeClock()
    notifier = FakeNotifier()
    outputs = []

    def fake_now() -> datetime:
        return datetime(2026, 10, 25, 11, 0)

    interval_loop(
        10,
        notifier,
        monotonic=clock.monotonic,
        sleep=clock.sleep,
        now=fake_now,
        out=outputs.append,
        iterations=2,
    )

    assert clock.sleeps == [10, 10]
    assert len(outputs) == 2


def test_interval_loop_handles_drift() -> None:
    clock = FakeClock()
    notifier = FakeNotifier()

    def slow_sleep(seconds: float) -> None:
        clock.sleeps.append(seconds)
        clock.now_value += seconds + 5

    interval_loop(
        10,
        notifier,
        monotonic=clock.monotonic,
        sleep=slow_sleep,
        now=lambda: datetime(2026, 10, 25, 11, 0),
        out=lambda _: None,
        iterations=2,
    )

    assert clock.sleeps[0] == 10
    assert len(clock.sleeps) == 2


def test_interval_schedule_advance() -> None:
    clock = FakeClock()
    schedule = IntervalSchedule.start(10, clock.monotonic)
    assert schedule.remaining(clock.monotonic()) == 10
    clock.now_value = 12
    schedule.advance(clock.monotonic())
    assert schedule.remaining(clock.monotonic()) == 8


def test_clock_schedule_start() -> None:
    now = datetime(2026, 10, 25, 9, 10)

    def fake_now() -> datetime:
        return now

    schedule = ClockSchedule.start(1800, fake_now)
    assert schedule.next_fire.hour == 9
    assert schedule.next_fire.minute == 30


def test_clock_next_boundary_15m_from_850() -> None:
    now = datetime(2026, 10, 25, 8, 50)
    target = next_clock_boundary(now, 900)
    assert target.hour == 9
    assert target.minute == 0


def test_clock_next_boundary_15m_from_905() -> None:
    now = datetime(2026, 10, 25, 9, 5)
    target = next_clock_boundary(now, 900)
    assert target.hour == 9
    assert target.minute == 15


def test_clock_next_boundary_15m_from_930() -> None:
    now = datetime(2026, 10, 25, 9, 30)
    target = next_clock_boundary(now, 900)
    assert target.hour == 9
    assert target.minute == 45


def test_clock_alignment_30m() -> None:
    now = datetime(2026, 10, 25, 9, 10)
    target = next_clock_boundary(now, 1800)
    assert target.hour == 9
    assert target.minute == 30


def test_clock_alignment_1h() -> None:
    now = datetime(2026, 10, 25, 9, 10)
    target = next_clock_boundary(now, 3600)
    assert target.hour == 10
    assert target.minute == 0


def test_clock_alignment_2h() -> None:
    now = datetime(2026, 10, 25, 9, 10)
    target = next_clock_boundary(now, 7200)
    assert target.hour == 10
    assert target.minute == 0


def test_clock_alignment_45m() -> None:
    now = datetime(2026, 10, 25, 9, 10)
    target = next_clock_boundary(now, 2700)
    assert target.hour == 9
    assert target.minute == 45


class WallClock:
    def __init__(self, start: datetime) -> None:
        self.current = start
        self.sleeps = []

    def now(self) -> datetime:
        return self.current

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.current = self.current + timedelta(seconds=seconds)


def test_clock_loop_waits_until_boundary() -> None:
    clock = WallClock(datetime(2026, 10, 25, 9, 30))
    notifier = FakeNotifier()
    outputs = []

    clock_loop(
        900,
        notifier,
        sleep=clock.sleep,
        now=clock.now,
        out=outputs.append,
        iterations=1,
    )

    assert clock.sleeps == [900]
    assert len(outputs) == 1


def test_clock_loop_skips_burst_after_delay() -> None:
    clock = WallClock(datetime(2026, 10, 25, 9, 0))
    notifier = FakeNotifier()
    outputs = []

    def slow_sleep(seconds: float) -> None:
        clock.sleeps.append(seconds)
        clock.current = clock.current + timedelta(seconds=seconds + 1800)

    clock_loop(
        900,
        notifier,
        sleep=slow_sleep,
        now=clock.now,
        out=outputs.append,
        iterations=1,
    )

    assert len(outputs) == 1


def test_run_schedule_stops_on_event() -> None:
    clock = FakeClock()
    notifier = FakeNotifier()
    stop_event = Event()
    stop_event.set()

    run_schedule(
        mode="interval",
        interval_seconds=10,
        notifier=notifier,
        monotonic=clock.monotonic,
        sleep=clock.sleep,
        now=lambda: datetime(2026, 10, 25, 11, 0),
        out=lambda _: None,
        stop_event=stop_event,
        iterations=1,
    )


def test_run_schedule_calls_callbacks() -> None:
    clock = FakeClock()
    notifier = FakeNotifier()
    fires = []
    nexts = []

    def fake_now() -> datetime:
        return datetime(2026, 10, 25, 11, 0)

    run_schedule(
        mode="interval",
        interval_seconds=10,
        notifier=notifier,
        monotonic=clock.monotonic,
        sleep=clock.sleep,
        now=fake_now,
        out=lambda _: None,
        on_fire=lambda ts, ok: fires.append((ts, ok)),
        on_next=lambda ts: nexts.append(ts),
        iterations=1,
    )

    assert len(fires) == 1
    assert len(nexts) >= 1
