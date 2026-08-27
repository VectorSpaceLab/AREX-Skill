#!/usr/bin/env python3
"""Validate a DeepFilterNet PipeWire filter-chain config without launching PipeWire."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable

KNOWN_LABELS = {"deep_filter_mono", "deep_filter_stereo"}
ATTEN_MIN = 0.0
ATTEN_MAX = 100.0

PLUGIN_RE = re.compile(
    r"(?m)^\s*plugin\s*=\s*(?P<value>\"[^\"]+\"|'[^']+'|[^\s\]}#,]+)"
)
LABEL_RE = re.compile(
    r"(?m)^\s*label\s*=\s*(?P<value>\"[^\"]+\"|'[^']+'|[A-Za-z0-9_.-]+)"
)
ATTEN_RE = re.compile(
    r"[\"']Attenuation\s+Limit\s+\(dB\)[\"']\s*(?:=|:)?\s*"
    r"(?P<value>[+-]?(?:\d+(?:\.\d*)?|\.\d+))"
)
RATE_RE = re.compile(r"(?m)^\s*audio\.rate\s*=\s*(?P<value>\d+)")


def strip_comments(text: str) -> str:
    """Remove simple PipeWire-template comments.

    The bundled templates use whole-line and trailing '#' comments only. This
    function intentionally avoids evaluating or expanding the config.
    """
    lines: list[str] = []
    for line in text.splitlines():
        lines.append(line.split("#", 1)[0])
    return "\n".join(lines)


def unquote(token: str) -> str:
    token = token.strip().rstrip(",")
    if len(token) >= 2 and token[0] == token[-1] and token[0] in {"'", '"'}:
        return token[1:-1]
    return token


def parse_float(value: str) -> float | None:
    try:
        return float(value)
    except ValueError:
        return None


def parse_int(value: str) -> int | None:
    try:
        return int(value)
    except ValueError:
        return None


def has_shell_expansion(path: str) -> bool:
    return path.startswith("~") or "$" in path


def format_list(items: Iterable[object]) -> str:
    return ", ".join(str(i) for i in items) if items else "<none>"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only validator for DeepFilterNet PipeWire filter-chain configs. "
            "Checks LADSPA plugin paths, labels, attenuation range, and 48 kHz rate; "
            "does not launch PipeWire or load plugins."
        )
    )
    parser.add_argument("config", type=Path, help="PipeWire filter-chain config to validate")
    parser.add_argument(
        "--expected-label",
        choices=sorted(KNOWN_LABELS),
        help="Require this LADSPA label, e.g. deep_filter_mono or deep_filter_stereo",
    )
    parser.add_argument(
        "--expected-plugin-path",
        help="Require every plugin path in the config to match this exact absolute path",
    )
    parser.add_argument(
        "--require-plugin-exists",
        action="store_true",
        help="Fail if the LADSPA plugin path does not exist on this machine",
    )
    parser.add_argument(
        "--expected-rate",
        type=int,
        default=48000,
        help="Expected audio.rate value when rate checking is enabled (default: 48000)",
    )
    parser.add_argument(
        "--skip-rate-check",
        action="store_true",
        help="Do not require audio.rate to match --expected-rate",
    )
    parser.add_argument("--quiet", action="store_true", help="Only print errors and warnings")
    return parser


def validate(args: argparse.Namespace) -> tuple[list[str], list[str], dict[str, object]]:
    errors: list[str] = []
    warnings: list[str] = []
    summary: dict[str, object] = {}

    config_path: Path = args.config
    if not config_path.is_file():
        return [f"config is not a readable file: {config_path}"], [], summary

    raw = config_path.read_text(encoding="utf-8")
    text = strip_comments(raw)

    plugin_paths = [unquote(m.group("value")) for m in PLUGIN_RE.finditer(text)]
    labels = [unquote(m.group("value")) for m in LABEL_RE.finditer(text)]
    atten_values_raw = [m.group("value") for m in ATTEN_RE.finditer(text)]
    rates_raw = [m.group("value") for m in RATE_RE.finditer(text)]

    summary["plugin_paths"] = plugin_paths
    summary["labels"] = labels
    summary["attenuation_values"] = atten_values_raw
    summary["audio_rates"] = rates_raw

    if not plugin_paths:
        errors.append("no `plugin = ...` LADSPA path found")
    for plugin in plugin_paths:
        if has_shell_expansion(plugin):
            errors.append(f"plugin path uses shell expansion; write an absolute path instead: {plugin}")
        if not Path(plugin).is_absolute():
            errors.append(f"plugin path is not absolute: {plugin}")
        expected_plugin_path = args.expected_plugin_path
        if expected_plugin_path:
            if not Path(expected_plugin_path).is_absolute():
                errors.append(f"--expected-plugin-path must be absolute: {expected_plugin_path}")
            if plugin != expected_plugin_path:
                errors.append(
                    f"plugin path mismatch: found {plugin!r}, expected {expected_plugin_path!r}"
                )
        if args.require_plugin_exists and not Path(plugin).is_file():
            errors.append(f"plugin file does not exist: {plugin}")
        elif not args.require_plugin_exists and not Path(plugin).exists():
            warnings.append(f"plugin path does not exist on this machine (not fatal): {plugin}")

    if not labels:
        errors.append("no `label = ...` LADSPA label found")
    unknown_labels = [label for label in labels if label not in KNOWN_LABELS]
    if unknown_labels:
        errors.append(
            "unknown LADSPA label(s): "
            f"{format_list(unknown_labels)}; expected one of {format_list(sorted(KNOWN_LABELS))}"
        )
    if args.expected_label and args.expected_label not in labels:
        errors.append(
            f"expected LADSPA label {args.expected_label!r}, found {format_list(labels)}"
        )

    if not atten_values_raw:
        errors.append('no `"Attenuation Limit (dB)"` control value found')
    for raw_value in atten_values_raw:
        value = parse_float(raw_value)
        if value is None:
            errors.append(f"attenuation value is not numeric: {raw_value!r}")
            continue
        if not (ATTEN_MIN <= value <= ATTEN_MAX):
            errors.append(
                f"attenuation value {value:g} outside allowed range {ATTEN_MIN:g}..{ATTEN_MAX:g}"
            )

    if not args.skip_rate_check:
        if not rates_raw:
            errors.append("no `audio.rate = ...` value found; expected 48000 for DeepFilterNet")
        else:
            rates: list[int] = []
            for raw_rate in rates_raw:
                rate = parse_int(raw_rate)
                if rate is None:
                    errors.append(f"audio.rate is not an integer: {raw_rate!r}")
                else:
                    rates.append(rate)
            mismatches = [rate for rate in rates if rate != args.expected_rate]
            if mismatches:
                errors.append(
                    f"audio.rate mismatch: found {format_list(rates)}, expected {args.expected_rate}"
                )

    return errors, warnings, summary


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    errors, warnings, summary = validate(args)

    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    if not args.quiet:
        print(f"OK: {args.config}")
        print(f"  plugin_paths: {format_list(summary.get('plugin_paths', []))}")
        print(f"  labels: {format_list(summary.get('labels', []))}")
        print(f"  attenuation_values: {format_list(summary.get('attenuation_values', []))}")
        if not args.skip_rate_check:
            print(f"  audio_rates: {format_list(summary.get('audio_rates', []))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
