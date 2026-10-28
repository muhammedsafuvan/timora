"""Persistent config storage for Timora."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import tempfile
from typing import Any

from platformdirs import user_config_path


@dataclass(frozen=True)
class ThemeConfig:
    """Theme selection stored in user config."""

    preset: str | None = None


def config_path() -> Path:
    """Return the config file path for Timora."""

    return user_config_path("timora") / "theme.json"


def load_theme_config() -> tuple[ThemeConfig, str | None]:
    """Load theme config, returning a warning when invalid."""

    path = config_path()
    if not path.exists():
        return ThemeConfig(), None

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ThemeConfig(), "Theme config is unreadable; using the default theme."

    if not isinstance(data, dict):
        return ThemeConfig(), "Theme config is invalid; using the default theme."

    preset = data.get("preset") if isinstance(data.get("preset"), str) else None

    return ThemeConfig(preset=preset), None


def save_theme_config(config: ThemeConfig) -> None:
    """Save theme config to disk atomically."""

    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "preset": config.preset,
    }
    temp_dir = path.parent
    with tempfile.NamedTemporaryFile("w", delete=False, dir=temp_dir, encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.flush()
        temp_path = Path(handle.name)
    temp_path.replace(path)
