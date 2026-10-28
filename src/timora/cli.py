"""Command-line interface for Timora."""

from __future__ import annotations

import argparse
import sys
from typing import TextIO

from timora.config import ThemeConfig, load_theme_config, save_theme_config
from timora.dashboard import run_dashboard
from timora.interval import parse_interval
from timora.notifier import VoiceNotifier
from timora.scheduler import run_schedule
from timora.theme import preset_names, resolve_theme


DEFAULT_INTERVAL_SECONDS = 3600
DEFAULT_MODE = "interval"


class TimoraArgumentParser(argparse.ArgumentParser):
	def parse_args(self, args: list[str] | None = None, namespace: argparse.Namespace | None = None) -> argparse.Namespace:
		parsed = super().parse_args(args, namespace)
		if parsed.interval is None:
			parsed.interval_seconds = DEFAULT_INTERVAL_SECONDS
		else:
			try:
				parsed.interval_seconds = parse_interval(parsed.interval)
			except ValueError as exc:
				self.error(str(exc))
		return parsed


def build_parser() -> argparse.ArgumentParser:
	parser = TimoraArgumentParser(prog="timora", description="Timora time reminders")
	parser.add_argument("--time", "-time", dest="interval", help="Interval (e.g. 30m, 45s, 2h)")
	parser.add_argument("--mode", choices=["interval", "clock"], default=DEFAULT_MODE)
	parser.add_argument("--no-ui", action="store_true", help="Disable the dashboard UI")
	parser.add_argument("--theme", choices=preset_names(), help="Theme preset name")
	return parser


def _should_use_ui(no_ui: bool, stdout: TextIO) -> bool:
	if no_ui:
		return False
	if not stdout.isatty():
		return False
	return sys.stdin.isatty()


def main(argv: list[str] | None = None) -> int:
	parser = build_parser()
	args = parser.parse_args(argv)
	notifier = VoiceNotifier()

	_, notice = load_theme_config()
	preset = args.theme

	try:
		selection = resolve_theme(preset_name=preset, primary_hex=None, secondary_hex=None)
	except ValueError:
		notice = "Theme config is invalid; using the default theme."
		selection = resolve_theme(preset_name=None, primary_hex=None, secondary_hex=None)

	if args.theme:
		save_theme_config(ThemeConfig(preset=selection.name))

	if _should_use_ui(args.no_ui, sys.stdout):
		return run_dashboard(
			interval_seconds=args.interval_seconds,
			mode=args.mode,
			notifier=notifier,
			theme_selection=selection,
			config_notice=notice,
		)

	if notice:
		print(notice, file=sys.stderr)

	run_schedule(
		mode=args.mode,
		interval_seconds=args.interval_seconds,
		notifier=notifier,
	)
	return 0


if __name__ == "__main__":  # pragma: no cover
	raise SystemExit(main())
