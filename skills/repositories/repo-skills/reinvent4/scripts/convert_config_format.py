#!/usr/bin/env python3
"""Convert REINVENT4 config files between TOML, JSON, and YAML when supported."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None  # type: ignore[assignment]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert REINVENT4 config files between TOML, JSON, and YAML without running REINVENT."
    )
    parser.add_argument("input", type=Path, help="Input config path.")
    parser.add_argument("output", type=Path, help="Output config path.")
    parser.add_argument(
        "--input-format",
        choices=("auto", "toml", "json", "yaml", "yml"),
        default="auto",
        help="Input format; auto uses the input suffix.",
    )
    parser.add_argument(
        "--output-format",
        choices=("auto", "json", "yaml", "yml"),
        default="auto",
        help="Output format; auto uses the output suffix. TOML output is not supported.",
    )
    parser.add_argument("--indent", type=int, default=2, help="JSON/YAML indentation.")
    return parser.parse_args()


def infer(path: Path, explicit: str) -> str:
    if explicit != "auto":
        return "yaml" if explicit == "yml" else explicit
    suffix = path.suffix.lower().lstrip(".")
    if suffix == "yml":
        return "yaml"
    if suffix in {"toml", "json", "yaml"}:
        return suffix
    raise SystemExit(f"Cannot infer format from suffix for {path}; pass --input-format/--output-format")


def load(path: Path, fmt: str) -> dict[str, Any]:
    if fmt == "toml":
        if tomllib is None:
            raise SystemExit("TOML input requires Python 3.11+ tomllib")
        with path.open("rb") as handle:
            return tomllib.load(handle)
    if fmt == "json":
        with path.open("r", encoding="utf-8") as handle:
            loaded = json.load(handle)
            if not isinstance(loaded, dict):
                raise SystemExit("REINVENT config root must be an object/table")
            return loaded
    if fmt == "yaml":
        try:
            import yaml  # type: ignore[import-not-found]
        except ModuleNotFoundError as exc:
            raise SystemExit("YAML input requires PyYAML") from exc
        with path.open("r", encoding="utf-8") as handle:
            loaded = yaml.safe_load(handle) or {}
            if not isinstance(loaded, dict):
                raise SystemExit("REINVENT config root must be a mapping")
            return loaded
    raise SystemExit(f"Unsupported input format: {fmt}")


def dump(data: dict[str, Any], path: Path, fmt: str, indent: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fmt == "json":
        path.write_text(json.dumps(data, indent=indent, sort_keys=False) + "\n", encoding="utf-8")
        return
    if fmt == "yaml":
        try:
            import yaml  # type: ignore[import-not-found]
        except ModuleNotFoundError as exc:
            raise SystemExit("YAML output requires PyYAML") from exc
        path.write_text(yaml.safe_dump(data, sort_keys=False, indent=indent), encoding="utf-8")
        return
    raise SystemExit("TOML output is not supported by this bundled helper; write JSON/YAML instead")


def main() -> int:
    args = parse_args()
    input_format = infer(args.input, args.input_format)
    output_format = infer(args.output, args.output_format)
    data = load(args.input, input_format)
    dump(data, args.output, output_format, args.indent)
    print(f"Converted {args.input} ({input_format}) -> {args.output} ({output_format})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
