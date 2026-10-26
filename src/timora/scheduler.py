"""Scheduling helpers for Timora."""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable, Union
from threading import Event

from timora.notifier import VoiceNotifier, build_announcement, format_timestamp


def _localize(now: datetime) -> datetime:
    if now.tzinfo is None:
        return now
    return now.astimezone()


def next_clock_boundary(now: datetime, interval_seconds: int) -> datetime:
    if interval_seconds <= 0:
        raise ValueError("Interval must be greater than zero.")

    local_now = _localize(now)
    midnight = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    elapsed = (local_now - midnight).total_seconds()
    intervals = int(elapsed // interval_seconds) + 1
    next_offset = intervals * interval_seconds
    return midnight + timedelta(seconds=next_offset)


@dataclass
class IntervalSchedule:
    interval_seconds: int
    next_fire_mono: float

    @classmethod
    def start(cls, interval_seconds: int, monotonic: Callable[[], float]) -> "IntervalSchedule":
        start_mono = monotonic()
        return cls(interval_seconds=interval_seconds, next_fire_mono=start_mono + interval_seconds)

    def remaining(self, now_mono: float) -> float:
        return self.next_fire_mono - now_mono

    def advance(self, now_mono: float) -> None:
        next_fire = self.next_fire_mono + self.interval_seconds
        if next_fire <= now_mono:
            next_fire = now_mono + self.interval_seconds
        self.next_fire_mono = next_fire


@dataclass
class ClockSchedule:
    interval_seconds: int
    next_fire: datetime

    @classmethod
    def start(cls, interval_seconds: int, now: Callable[[], datetime]) -> "ClockSchedule":
        current_time = now().astimezone()
        return cls(interval_seconds=interval_seconds, next_fire=next_clock_boundary(current_time, interval_seconds))

    def remaining(self, now_dt: datetime) -> float:
        return (self.next_fire - now_dt).total_seconds()

    def advance(self, now_dt: datetime) -> None:
        self.next_fire = next_clock_boundary(now_dt, self.interval_seconds)


ScheduleType = Union[IntervalSchedule, ClockSchedule]


def run_schedule(
    *,
    mode: str,
    interval_seconds: int,
    notifier: VoiceNotifier,
    monotonic: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
    now: Callable[[], datetime] = datetime.now,
    out: Callable[[str], None] = print,
    on_fire: Callable[[datetime, bool], None] | None = None,
    on_next: Callable[[datetime], None] | None = None,
    schedule: ScheduleType | None = None,
    iterations: int | None = None,
    stop_event: Event | None = None,
) -> None:
    count = 0
    if schedule is None:
        if mode == "clock":
            schedule = ClockSchedule.start(interval_seconds, now)
        else:
            schedule = IntervalSchedule.start(interval_seconds, monotonic)

    if on_next:
        if mode == "clock":
            on_next(schedule.next_fire)
        else:
            current_mono = monotonic()
            remaining = schedule.remaining(current_mono)
            on_next(now() + timedelta(seconds=max(0.0, remaining)))

    while True:
        if mode == "clock":
            current_time = now().astimezone()
            delay = schedule.remaining(current_time)
        else:
            current_mono = monotonic()
            delay = schedule.remaining(current_mono)

        if delay > 0:
            if stop_event is not None:
                if stop_event.wait(delay):
                    return
            else:
                sleep(delay)

        fired_time = now().astimezone()
        if mode == "clock" and fired_time < schedule.next_fire:
            continue

        if mode == "interval":
            current_mono = monotonic()
            if schedule.remaining(current_mono) > 0:
                continue

        if stop_event is not None and stop_event.is_set():
            return

        message = build_announcement(fired_time)
        out(f"[{format_timestamp(fired_time)}] {message}")

        speech_ok = False
        if notifier.is_available():
            speech_ok = notifier.speak(message)
            if not speech_ok:
                out("Speech failed; continuing with text only.")

        if on_fire:
            on_fire(fired_time, speech_ok)

        count += 1
        if iterations is not None and count >= iterations:
            return

        if mode == "clock":
            schedule.advance(fired_time)
            if on_next:
                on_next(schedule.next_fire)
        else:
            current_mono = monotonic()
            schedule.advance(current_mono)
            if on_next:
                remaining = schedule.remaining(current_mono)
                on_next(fired_time + timedelta(seconds=max(0.0, remaining)))


def interval_loop(
    interval_seconds: int,
    notifier: VoiceNotifier,
    *,
    monotonic: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
    now: Callable[[], datetime] = datetime.now,
    out: Callable[[str], None] = print,
    iterations: int | None = None,
) -> None:
    run_schedule(
        mode="interval",
        interval_seconds=interval_seconds,
        notifier=notifier,
        monotonic=monotonic,
        sleep=sleep,
        now=now,
        out=out,
        iterations=iterations,
    )


def clock_loop(
    interval_seconds: int,
    notifier: VoiceNotifier,
    *,
    sleep: Callable[[float], None] = time.sleep,
    now: Callable[[], datetime] = datetime.now,
    out: Callable[[str], None] = print,
    iterations: int | None = None,
) -> None:
    run_schedule(
        mode="clock",
        interval_seconds=interval_seconds,
        notifier=notifier,
        sleep=sleep,
        now=now,
        out=out,
        iterations=iterations,
    )
