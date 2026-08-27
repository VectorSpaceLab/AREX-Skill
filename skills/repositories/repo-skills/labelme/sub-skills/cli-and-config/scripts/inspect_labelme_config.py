#!/usr/bin/env python3
"""Inspect a labelme Config File or YAML override string.

This helper uses the installed labelme package to apply the same default merge,
legacy-key migration, and validation rules that the application uses. It does not
write the Config File.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _compact(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _compact(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_compact(v) for v in value]
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--config-file", type=Path, help="Config File path, e.g. ~/.labelmerc")
    group.add_argument("--config-yaml", help="inline YAML overrides as accepted by labelme --config")
    parser.add_argument("--show", choices=["all", "labels", "shortcuts", "ai", "shape-color"], default="all")
    args = parser.parse_args()

    try:
        from labelme import _config
        from labelme import _yaml
    except Exception as exc:
        print(f"ERROR: labelme must be installed in this Python: {type(exc).__name__}: {exc}")
        return 2

    config_file = args.config_file
    overrides: dict[str, Any] = {}
    if args.config_yaml:
        loaded = _yaml.safe_load(args.config_yaml)
        if not isinstance(loaded, dict):
            print("ERROR: --config-yaml must parse to a YAML mapping")
            return 2
        overrides = loaded

    try:
        config = _config.load_config(config_file=config_file, config_overrides=overrides)
    except Exception as exc:
        print(f"ERROR: config is not valid for labelme: {type(exc).__name__}: {exc}")
        return 1

    selectors = {
        "all": config,
        "labels": {"labels": config.get("labels"), "flags": config.get("flags"), "label_flags": config.get("label_flags"), "validate_label": config.get("validate_label")},
        "shortcuts": config.get("shortcuts"),
        "ai": config.get("ai"),
        "shape-color": config.get("shape_color"),
    }
    print(json.dumps(_compact(selectors[args.show]), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
