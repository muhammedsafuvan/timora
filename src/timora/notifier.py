"""Voice and formatting helpers for Timora."""

from __future__ import annotations

import shutil
import subprocess
import sys
from datetime import datetime


def _is_macos() -> bool:
    return sys.platform == "darwin"


def _resolve_say_command() -> str | None:
    if not _is_macos():
        return None
    return shutil.which("say")


class VoiceNotifier:
    """Simple macOS voice notifier using the system `say` command."""

    def __init__(self) -> None:
        self._say_cmd = _resolve_say_command()

    def is_available(self) -> bool:
        return self._say_cmd is not None

    def speak(self, message: str) -> bool:
        if not self._say_cmd:
            return False

        try:
            subprocess.run([self._say_cmd, message], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except (OSError, subprocess.CalledProcessError):
            return False

        return True


def format_timestamp(now: datetime) -> str:
    hour = now.hour % 12 or 12
    ampm = "AM" if now.hour < 12 else "PM"
    return f"{hour}:{now.minute:02d} {ampm}"


def spoken_time(now: datetime) -> str:
    hour = now.hour % 12 or 12
    ampm = "AM" if now.hour < 12 else "PM"
    if now.minute == 0:
        return f"{hour} {ampm}"
    return f"{hour}:{now.minute:02d} {ampm}"


def build_announcement(now: datetime) -> str:
    return f"It is {spoken_time(now)}."
