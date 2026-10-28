from timora.theme import build_theme, normalize_hex, preset_names, resolve_theme


def test_normalize_hex_expands_short() -> None:
    assert normalize_hex("#abc") == "#aabbcc"
    assert normalize_hex("#A1B2C3") == "#a1b2c3"


def test_build_theme_rejects_invalid() -> None:
    try:
        build_theme("red")
    except ValueError as exc:
        assert "hex" in str(exc).lower()
    else:
        raise AssertionError("Expected ValueError")


def test_resolve_theme_uses_preset() -> None:
    presets = preset_names()
    selection = resolve_theme(preset_name=presets[0], primary_hex=None, secondary_hex=None)
    assert selection.is_preset is True


def test_build_theme_contrast() -> None:
    theme = build_theme("#4fc3ff")
    bg = _hex_to_rgb(theme.background)
    accent = _hex_to_rgb(theme.accent)
    assert _contrast_ratio(bg, accent) >= 4.5


def _hex_to_rgb(value: str) -> tuple[float, float, float]:
    value = normalize_hex(value)
    return (int(value[1:3], 16) / 255.0, int(value[3:5], 16) / 255.0, int(value[5:7], 16) / 255.0)


def _luminance_channel(channel: float) -> float:
    if channel <= 0.03928:
        return channel / 12.92
    return ((channel + 0.055) / 1.055) ** 2.4


def _relative_luminance(rgb: tuple[float, float, float]) -> float:
    red, green, blue = rgb
    return 0.2126 * _luminance_channel(red) + 0.7152 * _luminance_channel(green) + 0.0722 * _luminance_channel(blue)


def _contrast_ratio(left: tuple[float, float, float], right: tuple[float, float, float]) -> float:
    lum_left = _relative_luminance(left)
    lum_right = _relative_luminance(right)
    lighter = max(lum_left, lum_right)
    darker = min(lum_left, lum_right)
    return (lighter + 0.05) / (darker + 0.05)
