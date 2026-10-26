import pytest

from timora import cli as cli_module

from timora.cli import DEFAULT_INTERVAL_SECONDS, DEFAULT_MODE, build_parser


def test_default_interval_seconds() -> None:
    parser = build_parser()
    args = parser.parse_args([])
    assert args.interval_seconds == DEFAULT_INTERVAL_SECONDS
    assert args.mode == DEFAULT_MODE


def test_time_alias_parses() -> None:
    parser = build_parser()
    args = parser.parse_args(["-time", "30m"])
    assert args.interval_seconds == 1800


@pytest.mark.parametrize("mode", ["interval", "clock"])
def test_mode_parses(mode: str) -> None:
    parser = build_parser()
    args = parser.parse_args(["--mode", mode])
    assert args.mode == mode


def test_help_output(capsys: pytest.CaptureFixture[str]) -> None:
    parser = build_parser()
    parser.print_help()
    captured = capsys.readouterr()
    assert "--time" in captured.out
    assert "--mode" in captured.out
    assert "--no-ui" in captured.out
    assert "timora" in captured.out


def test_invalid_interval_exits(capsys: pytest.CaptureFixture[str]) -> None:
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--time", "abc"])
    captured = capsys.readouterr()
    assert "Interval" in captured.err


def test_invalid_mode_exits(capsys: pytest.CaptureFixture[str]) -> None:
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--mode", "nope"])
    captured = capsys.readouterr()
    assert "invalid choice" in captured.err


def test_no_ui_flag_parses() -> None:
    parser = build_parser()
    args = parser.parse_args(["--no-ui"])
    assert args.no_ui is True


def test_should_use_ui_respects_no_ui(monkeypatch: pytest.MonkeyPatch) -> None:
    class DummyStream:
        def isatty(self) -> bool:
            return True

    dummy = DummyStream()
    monkeypatch.setattr(cli_module.sys, "stdin", dummy)
    assert cli_module._should_use_ui(True, dummy) is False


def test_should_use_ui_requires_tty(monkeypatch: pytest.MonkeyPatch) -> None:
    class DummyStream:
        def __init__(self, value: bool) -> None:
            self._value = value

        def isatty(self) -> bool:
            return self._value

    stdout = DummyStream(True)
    stdin = DummyStream(False)
    monkeypatch.setattr(cli_module.sys, "stdin", stdin)
    assert cli_module._should_use_ui(False, stdout) is False
