# Timora

Timora is a lightweight CLI time reminder with optional voice announcements and a minimal dashboard UI.

<img width="1504" height="921" alt="image" src="https://github.com/user-attachments/assets/9656f12e-0b49-4bc5-8dbf-2b81929b4b03" />


## Requirements

- Python 3.9 or newer
- macOS for voice output (uses the built-in `say` command)

## Installation

```bash
python -m pip install timora
```

## Usage

Run with the default one-hour interval in interval mode:

```bash
timora
```

Set a custom interval:

```bash
timora --time 30m
timora --time 15m
timora --time 2h
timora --time 45s
```

A single-dash alias is also available:

```bash
timora -time 30m
```

Choose a scheduling mode:

```bash
timora --time 15m --mode interval
timora --time 15m --mode clock
```

Disable the dashboard UI:

```bash
timora --no-ui
```

Choose a theme preset (default is `mint`):

```bash
timora --theme violet
```

### Arguments

- `--time`, `-time`: Interval (examples: `30m`, `45s`, `2h`).
- `--mode`: Scheduling mode: `interval` or `clock`.
- `--theme`: Theme preset name. Available: `mint`, `red`, `green`, `blue`, `amber`, `violet`, `rose`, `slate`.
- `--no-ui`: Disable the Textual dashboard UI.

### Interval formats

- `30s` for seconds
- `15m` for minutes
- `1h` for hours
- A plain positive integer like `30` is treated as minutes

Invalid, zero, or negative values are rejected with a helpful error.

### Scheduling modes

- `interval`: reminders occur relative to startup time.
- `clock`: reminders align to wall-clock boundaries.

Clock alignment follows multiples of the interval since local midnight. For example:

- `15m`: minute 00, 15, 30, 45
- `30m`: minute 00, 30
- `1h`: minute 00 of each hour
- `2h`: 00:00, 02:00, 04:00, ...
- `45m`: 00:00, 00:45, 01:30, 02:15, ...

## Dashboard UI

When running in an interactive terminal, Timora shows a minimal Textual dashboard with:

- Live local clock and date
- Time zone label (IANA name when available), abbreviation, and UTC offset
- Next reminder time with countdown and progress bar
- Interval and scheduling mode
- Recent announcements history

The IANA timezone identifier (for example, `Asia/Kolkata`) describes the regional time rules used to compute local time. It does not indicate server location.

If standard output is redirected or the terminal is non-interactive, Timora automatically falls back to plain text output.

## Voice support

Timora uses macOS `say` for offline speech. On non-macOS platforms, Timora falls back to text-only announcements and prints a notice that speech is unavailable.
