from datetime import datetime

from timora.notifier import VoiceNotifier, build_announcement, format_timestamp, spoken_time


def test_time_formatting() -> None:
    dt = datetime(2026, 10, 25, 11, 0)
    assert format_timestamp(dt) == "11:00 AM"
    assert spoken_time(dt) == "11 AM"
    assert build_announcement(dt) == "It is 11 AM."


def test_time_formatting_minutes() -> None:
    dt = datetime(2026, 10, 25, 23, 5)
    assert format_timestamp(dt) == "11:05 PM"
    assert spoken_time(dt) == "11:05 PM"


def test_voice_notifier_unavailable(monkeypatch) -> None:
    notifier = VoiceNotifier()
    monkeypatch.setattr(notifier, "_say_cmd", None)
    assert notifier.is_available() is False
    assert notifier.speak("Hello") is False
