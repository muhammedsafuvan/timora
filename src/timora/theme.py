"""Theme building and preset utilities for Timora."""

from __future__ import annotations

from dataclasses import dataclass
import colorsys
import re
from typing import Iterable


_HEX_RE = re.compile(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
_MIN_CONTRAST = 4.5


@dataclass(frozen=True)
class Theme:
    """Semantic color roles for the dashboard."""

    accent: str
    secondary: str
    background: str
    surface_border: str
    track: str
    muted: str
    text: str


@dataclass(frozen=True)
class ThemePreset:
    """User-visible theme preset data."""

    name: str
    primary: str | None = None
    secondary: str | None = None
    theme: Theme | None = None


@dataclass(frozen=True)
class ThemeSelection:
    """Resolved theme selection for the dashboard."""

    name: str
    theme: Theme
    primary: str | None
    secondary: str | None
    is_preset: bool


_PRESET_DATA: list[dict[str, object]] = [
    {
        "name": "mint",
        "theme": {
            "accent": "#8fe3c4",
            "secondary": "#a9b8b0",
            "background": "#0b100e",
            "surface_border": "#22302a",
            "track": "#2b3a37",
            "muted": "#7f8f87",
            "text": "#ffffff",
        },
    },
    {"name": "red", "primary": "#ff4d4d", "secondary": "#ffb3b3"},
    {"name": "green", "primary": "#4dbb7f", "secondary": "#b6e6cf"},
    {"name": "blue", "primary": "#4fc3ff", "secondary": "#bfe9ff"},
    {"name": "amber", "primary": "#ffb020", "secondary": "#ffe0a6"},
    {"name": "violet", "primary": "#7b61ff", "secondary": "#cbbcff"},
    {"name": "rose", "primary": "#ff6ea8", "secondary": "#ffb9d3"},
    {"name": "slate", "primary": "#5b6f7d", "secondary": "#c7d0d6"},
]


def normalize_hex(value: str) -> str:
    """Normalize a hex color string to #rrggbb lowercase."""

    if value is None:
        raise ValueError("Color value is required.")
    text = value.strip()
    if not _HEX_RE.fullmatch(text):
        raise ValueError("Color must be a hex value like #abc or #aabbcc.")
    if len(text) == 4:
        text = "#" + "".join(char * 2 for char in text[1:])
    return text.lower()


def build_theme(primary_hex: str) -> Theme:
    """Build a cohesive theme derived from a single primary color."""

    primary = normalize_hex(primary_hex)
    primary_rgb = _hex_to_rgb(primary)
    hue, lightness, saturation = colorsys.rgb_to_hls(*primary_rgb)

    background = _hls_to_hex(hue, 0.06, 0.08)
    surface_border = _hls_to_hex(hue, 0.16, 0.1)
    track = _hls_to_hex(hue, 0.26, 0.12)

    secondary_shade, muted = _secondary_shades(primary)
    accent = _accent_from_primary(hue, lightness, saturation, background)

    return Theme(
        accent=accent,
        secondary=secondary_shade,
        background=background,
        surface_border=surface_border,
        track=track,
        muted=muted,
        text="#ffffff",
    )


def list_presets() -> list[ThemePreset]:
    """Return all available theme presets."""

    presets: list[ThemePreset] = []
    for entry in _PRESET_DATA:
        theme_data = entry.get("theme")
        theme = None
        if isinstance(theme_data, dict):
            theme = Theme(**{key: str(value) for key, value in theme_data.items()})
        presets.append(
            ThemePreset(
                name=str(entry.get("name")),
                primary=entry.get("primary") if isinstance(entry.get("primary"), str) else None,
                secondary=entry.get("secondary") if isinstance(entry.get("secondary"), str) else None,
                theme=theme,
            )
        )
    return presets


def preset_names() -> list[str]:
    """Return preset names in display order."""

    return [preset.name for preset in list_presets()]


def resolve_theme(
    *,
    preset_name: str | None,
    primary_hex: str | None,
    secondary_hex: str | None,
) -> ThemeSelection:
    """Resolve a theme from preset inputs."""

    if primary_hex or secondary_hex:
        raise ValueError("Custom colors are disabled; choose a preset theme.")

    presets = list_presets()
    if preset_name:
        for preset in presets:
            if preset.name == preset_name:
                theme = preset.theme or build_theme(preset.primary or "#8fe3c4")
                return ThemeSelection(
                    name=preset.name,
                    theme=theme,
                    primary=preset.primary,
                    secondary=preset.secondary,
                    is_preset=True,
                )
        raise ValueError(f"Unknown theme preset '{preset_name}'.")

    default_preset = presets[0]
    theme = default_preset.theme or build_theme(default_preset.primary or "#8fe3c4")
    return ThemeSelection(
        name=default_preset.name,
        theme=theme,
        primary=default_preset.primary,
        secondary=default_preset.secondary,
        is_preset=True,
    )


def _secondary_shades(primary_hex: str) -> tuple[str, str]:
    primary = normalize_hex(primary_hex)
    red, green, blue = _hex_to_rgb(primary)
    hue, lightness, saturation = colorsys.rgb_to_hls(red, green, blue)
    secondary_shade = _hls_to_hex(hue, _clamp(lightness, 0.6, 0.8), _clamp(saturation, 0.12, 0.3))
    muted = _hls_to_hex(hue, _clamp(lightness, 0.45, 0.65), _clamp(saturation, 0.08, 0.25))
    return secondary_shade, muted


def _accent_from_primary(hue: float, lightness: float, saturation: float, background_hex: str) -> str:
    accent_lightness = _clamp(lightness, 0.55, 0.75)
    accent_saturation = _clamp(max(saturation, 0.35), 0.35, 0.95)
    background_rgb = _hex_to_rgb(background_hex)

    for step in range(0, 20):
        candidate_lightness = _clamp(accent_lightness + step * 0.02, 0.0, 0.95)
        accent_rgb = colorsys.hls_to_rgb(hue, candidate_lightness, accent_saturation)
        if _contrast_ratio(accent_rgb, background_rgb) >= _MIN_CONTRAST:
            return _rgb_to_hex(accent_rgb)

    return _rgb_to_hex(colorsys.hls_to_rgb(hue, accent_lightness, accent_saturation))


def _hex_to_rgb(value: str) -> tuple[float, float, float]:
    text = normalize_hex(value)
    red = int(text[1:3], 16) / 255.0
    green = int(text[3:5], 16) / 255.0
    blue = int(text[5:7], 16) / 255.0
    return red, green, blue


def _rgb_to_hex(rgb: Iterable[float]) -> str:
    red, green, blue = (int(round(_clamp(channel, 0.0, 1.0) * 255.0)) for channel in rgb)
    return f"#{red:02x}{green:02x}{blue:02x}"


def _hls_to_hex(hue: float, lightness: float, saturation: float) -> str:
    return _rgb_to_hex(colorsys.hls_to_rgb(hue, lightness, saturation))


def _luminance_channel(channel: float) -> float:
    if channel <= 0.03928:
        return channel / 12.92
    return ((channel + 0.055) / 1.055) ** 2.4


def _relative_luminance(rgb: Iterable[float]) -> float:
    red, green, blue = rgb
    return 0.2126 * _luminance_channel(red) + 0.7152 * _luminance_channel(green) + 0.0722 * _luminance_channel(blue)


def _contrast_ratio(foreground: Iterable[float], background: Iterable[float]) -> float:
    lum_fore = _relative_luminance(foreground)
    lum_back = _relative_luminance(background)
    lighter = max(lum_fore, lum_back)
    darker = min(lum_fore, lum_back)
    return (lighter + 0.05) / (darker + 0.05)


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))
