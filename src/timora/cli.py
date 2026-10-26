"""Command-line interface for Timora."""

from __future__ import annotations

import argparse
import sys
from typing import TextIO

from timora.interval import format_interval, parse_interval
from timora.notifier import VoiceNotifier
from timora.scheduler import clock_loop, interval_loop

DEFAULT_INTERVAL_SECONDS = 3600
DEFAULT_MODE = "interval"
SUPPORTED_MODES = ("interval", "clock")


def _interval_arg(value: str) -> int:
    try:
        return parse_interval(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="timora",
        description="Voice time reminders at a configurable interval.",
    )
    parser.add_argument(
        "-time",
        "--time",
        dest="interval_seconds",
        type=_interval_arg,
        default=DEFAULT_INTERVAL_SECONDS,
        metavar="INTERVAL",
        help=(
            "Reminder interval like 30s, 15m, 1h, or a plain positive integer "
            "for minutes. Default: 1h."
        ),
    )
    parser.add_argument(
        "--mode",
        dest="mode",
        choices=SUPPORTED_MODES,
        default=DEFAULT_MODE,
        help="Scheduling mode: interval or clock. Default: interval.",
    )
    parser.add_argument(
        "--no-ui",
        action="store_true",
        help="Disable the dashboard UI and use plain text output.",
    )
    return parser


def _should_use_ui(no_ui: bool, stdout: TextIO | None) -> bool:
    if no_ui:
        return False
    stream = stdout if stdout is not None else sys.stdout
    return stream.isatty() and sys.stdin.isatty()


def main(stdout: TextIO | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args()

    interval_seconds = args.interval_seconds
    interval_label = format_interval(interval_seconds)
    mode = args.mode
    notifier = VoiceNotifier()
    no_ui = args.no_ui

    stream = stdout.write if stdout else print

    if _should_use_ui(no_ui, stdout):
        try:
            from timora.dashboard import run_dashboard

            return run_dashboard(interval_seconds=interval_seconds, mode=mode, notifier=notifier)
        except Exception as exc:
            stream(f"Dashboard unavailable ({exc}); using text output.\n")

    stream("Timora is running.\n")
    stream(f"Reminder interval: {interval_label}.\n")
    stream(f"Scheduling mode: {mode}.\n")
    stream("Press Ctrl+C to stop.\n\n")

    if not notifier.is_available():
        stream("Voice announcements are unavailable; using text only.\n\n")

    try:
        if mode == "clock":
            clock_loop(interval_seconds, notifier, out=print)
        else:
            interval_loop(interval_seconds, notifier, out=print)
    except KeyboardInterrupt:
        stream("Timora stopped.\n")
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
