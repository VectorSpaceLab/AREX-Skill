#!/usr/bin/env python3
"""Validate and summarize an XLNet config JSON without importing TensorFlow."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REQUIRED_KEYS = (
    "n_layer",
    "d_model",
    "n_head",
    "d_head",
    "d_inner",
    "ff_activation",
    "untie_r",
    "n_token",
)
SUMMARY_KEYS = (
    "n_layer",
    "d_model",
    "n_head",
    "d_head",
    "d_inner",
    "ff_activation",
    "untie_r",
    "n_token",
)


def load_config(path: Path):
    """Load and validate a single config JSON file."""

    try:
        raw_text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise OSError(f"cannot read {path}: {exc}") from exc

    try:
        config = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"invalid JSON: {exc.msg} (line {exc.lineno}, column {exc.colno})"
        ) from exc

    if not isinstance(config, dict):
        raise ValueError("top-level JSON value must be an object")

    missing = [key for key in REQUIRED_KEYS if key not in config]
    if missing:
        raise ValueError(f"missing required key(s): {', '.join(missing)}")

    return config


def summarize(path: Path, config):
    """Format a concise one-line summary."""

    values = " ".join(f"{key}={config[key]}" for key in SUMMARY_KEYS)
    return f"OK {path}: {values}"


def build_arg_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Validate an XLNet config JSON and print a concise summary of the "
            "required model fields."
        )
    )
    parser.add_argument(
        "config_json",
        nargs="+",
        help="Path(s) to xlnet_config.json files to validate.",
    )
    return parser


def main(argv=None):
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    exit_code = 0
    for raw_path in args.config_json:
        path = Path(raw_path)
        try:
            config = load_config(path)
        except Exception as exc:  # pylint: disable=broad-except
            print(f"ERROR {path}: {exc}", file=sys.stderr)
            exit_code = 2
            continue
        print(summarize(path, config))

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
