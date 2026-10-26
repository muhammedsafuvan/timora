import pytest

from timora.interval import format_interval, parse_interval


def test_default_interval_label() -> None:
    assert format_interval(3600) == "1 hour"


def test_parse_seconds_minutes_hours() -> None:
    assert parse_interval("30s") == 30
    assert parse_interval("15m") == 900
    assert parse_interval("2h") == 7200


def test_parse_plain_integer_as_minutes() -> None:
    assert parse_interval("30") == 1800


@pytest.mark.parametrize("value", ["0", "-1", "", "abc", "1x", "10q"])
def test_parse_invalid(value: str) -> None:
    with pytest.raises(ValueError):
        parse_interval(value)
