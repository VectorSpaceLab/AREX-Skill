#!/usr/bin/env python3
"""Validate common PaddleViT classification YAML without importing the checkout."""
from __future__ import annotations
import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Mapping


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a PaddleViT classification YAML without source imports, downloads, or training."
    )
    parser.add_argument("--config", required=True, type=Path, help="YAML config path")
    parser.add_argument("--require", action="append", default=[], metavar="PATH", help="Required dotted key, repeatable")
    parser.add_argument("--allow-missing-sections", action="store_true", help="Do not require DATA and MODEL sections")
    parser.add_argument("--json", action="store_true", help="Emit deterministic JSON")
    return parser.parse_args()


def load_yaml(path: Path) -> Mapping[str, Any]:
    try:
        import yaml
    except ModuleNotFoundError as exc:
        raise RuntimeError("PyYAML is required; install it with `python -m pip install pyyaml`.") from exc
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise RuntimeError(f"Cannot read {path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise RuntimeError(f"Invalid YAML in {path}: {exc}") from exc
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise RuntimeError("Top-level YAML value must be a mapping.")
    return raw


def get_path(data: Mapping[str, Any], dotted: str) -> Any:
    value: Any = data
    for part in dotted.split("."):
        if not isinstance(value, Mapping) or part not in value:
            raise KeyError(dotted)
        value = value[part]
    return value


def positive(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value > 0


def validate(data: Mapping[str, Any], allow_missing_sections: bool, required: list[str]) -> list[str]:
    errors: list[str] = []
    for section in ("DATA", "MODEL"):
        if section not in data and not allow_missing_sections:
            errors.append(f"missing required top-level section: {section}")
        elif section in data and not isinstance(data[section], Mapping):
            errors.append(f"{section} must be a mapping")
    for dotted in required:
        try:
            get_path(data, dotted)
        except KeyError:
            errors.append(f"missing required key: {dotted}")
    for dotted in ("DATA.IMAGE_SIZE", "DATA.CROP_PCT", "DATA.BATCH_SIZE", "DATA.IMAGE_CHANNELS", "MODEL.NUM_CLASSES"):
        try:
            value = get_path(data, dotted)
        except KeyError:
            continue
        if not positive(value):
            errors.append(f"{dotted} must be a finite positive number, got {value!r}")
    for dotted in ("MODEL.TYPE", "MODEL.NAME"):
        try:
            value = get_path(data, dotted)
        except KeyError:
            continue
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{dotted} must be a non-empty string, got {value!r}")
    try:
        base = get_path(data, "BASE")
        if not isinstance(base, (str, list)):
            errors.append("BASE must be a string or list when present")
    except KeyError:
        pass
    return errors


def main() -> int:
    args = parse_args()
    try:
        data = load_yaml(args.config)
        errors = validate(data, args.allow_missing_sections, args.require)
        selected = {}
        for dotted in ("BASE", "DATA.DATASET", "DATA.IMAGE_SIZE", "DATA.IMAGE_CHANNELS", "DATA.CROP_PCT", "DATA.BATCH_SIZE", "MODEL.TYPE", "MODEL.NAME", "MODEL.NUM_CLASSES"):
            try:
                selected[dotted] = get_path(data, dotted)
            except KeyError:
                pass
        report = {"config": str(args.config.resolve()), "ok": not errors, "selected": selected, "errors": errors}
    except RuntimeError as exc:
        report = {"config": str(args.config), "ok": False, "selected": {}, "errors": [str(exc)]}
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    elif report["ok"]:
        print(f"OK: {report['config']}")
        for key, value in report["selected"].items():
            print(f"  {key} = {value!r}")
    else:
        print(f"INVALID: {report['config']}", file=sys.stderr)
        for error in report["errors"]:
            print(f"  - {error}", file=sys.stderr)
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
