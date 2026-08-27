#!/usr/bin/env python3
"""Read-only CLI and checkpoint path preflight for Gaussian-SLAM evaluation.

This deliberately performs no repository imports, checkpoint deserialization,
network access, GUI creation, or writes. It checks only paths and a small set
of configuration keys in text.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


_REQUIRED_CONFIG_KEYS = ("dataset_name", "data", "cam")


def _config_key_present(text: str, key: str) -> bool:
    """Accept common YAML top-level or nested key spellings without parsing."""
    return re.search(rf"(?m)^\s*{re.escape(key)}\s*:", text) is not None


def inspect(checkpoint: Path, config: Path | None) -> dict[str, Any]:
    resolved_checkpoint = checkpoint.expanduser()
    result: dict[str, Any] = {
        "checkpoint": str(resolved_checkpoint),
        "checkpoint_exists": resolved_checkpoint.is_dir(),
        "config": None,
        "config_exists": False,
        "required_files": {},
        "submap_count": 0,
        "warnings": [],
        "errors": [],
    }

    if not resolved_checkpoint.is_dir():
        result["errors"].append("checkpoint is not an existing directory")
        return result

    config_path = (config.expanduser() if config else resolved_checkpoint / "config.yaml")
    result["config"] = str(config_path)
    result["config_exists"] = config_path.is_file()
    if not config_path.is_file():
        result["errors"].append("config file is missing")
    else:
        try:
            text = config_path.read_text(encoding="utf-8")
        except OSError as exc:
            result["errors"].append(f"config cannot be read: {exc}")
        else:
            result["config_keys"] = {
                key: _config_key_present(text, key) for key in _REQUIRED_CONFIG_KEYS
            }
            missing = [key for key, present in result["config_keys"].items() if not present]
            if missing:
                result["warnings"].append(
                    "config text does not visibly contain: " + ", ".join(missing)
                )

    for name in ("estimated_c2w.ckpt",):
        path = resolved_checkpoint / name
        result["required_files"][name] = path.is_file()
        if not path.is_file():
            result["errors"].append(f"required file is missing: {name}")

    submaps = resolved_checkpoint / "submaps"
    if not submaps.is_dir():
        result["errors"].append("submaps directory is missing")
    else:
        files = sorted(submaps.glob("*.ckpt"))
        result["submap_count"] = len(files)
        if not files:
            result["errors"].append("submaps directory has no .ckpt files")
        result["submaps"] = [path.name for path in files]

    if not result["errors"] and result.get("warnings"):
        result["status"] = "warning"
    elif result["errors"]:
        result["status"] = "error"
    else:
        result["status"] = "ok"
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only path/config preflight; never loads checkpoints."
    )
    parser.add_argument("--checkpoint", required=True, type=Path)
    parser.add_argument(
        "--config", type=Path, help="Config path (default: CHECKPOINT/config.yaml)"
    )
    parser.add_argument("--json", action="store_true", help="Print JSON instead of text")
    args = parser.parse_args(argv)
    result = inspect(args.checkpoint, args.config)

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"status: {result['status']}")
        print(f"checkpoint: {result['checkpoint']}")
        print(f"config: {result.get('config')}")
        print(f"submaps: {result.get('submap_count', 0)}")
        for warning in result.get("warnings", []):
            print(f"warning: {warning}")
        for error in result.get("errors", []):
            print(f"error: {error}")
    return 0 if result["status"] != "error" else 2


if __name__ == "__main__":
    sys.exit(main())
