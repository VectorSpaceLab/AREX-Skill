#!/usr/bin/env python3
"""Validate the file-level Gaussian-SLAM checkpoint contract, read-only.

No torch/Open3D/project imports are used, so this tool is safe on CPU-only
machines. It does not deserialize, rewrite, or repair any checkpoint. Payload
keys inside .ckpt files require a compatible project environment and are
reported as an explicit unverified boundary here.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


def _yaml_scalar(text: str, key: str) -> str | None:
    match = re.search(rf"(?m)^\s*{re.escape(key)}\s*:\s*([^#\n]+)", text)
    if not match:
        return None
    return match.group(1).strip().strip('"\'')


def validate(checkpoint: Path, config_path: Path | None = None) -> dict[str, Any]:
    checkpoint = checkpoint.expanduser()
    result: dict[str, Any] = {
        "checkpoint": str(checkpoint),
        "status": "ok",
        "errors": [],
        "warnings": [],
        "unverified": [
            "serialized .ckpt payloads were not deserialized; tensor devices and keys are unverified"
        ],
    }
    if not checkpoint.is_dir():
        result["errors"].append("checkpoint is not an existing directory")
        result["status"] = "error"
        return result

    config = (config_path.expanduser() if config_path else checkpoint / "config.yaml")
    result["config"] = str(config)
    if not config.is_file():
        result["errors"].append("config.yaml (or explicit config) is missing")
    else:
        text = config.read_text(encoding="utf-8")
        result["dataset_name"] = _yaml_scalar(text, "dataset_name")
        result["scene_name"] = _yaml_scalar(text, "scene_name")
        if result["dataset_name"] is None:
            result["errors"].append("dataset_name is not visible in config")
        if result["scene_name"] is None:
            result["warnings"].append("data.scene_name is not visible in config")
        if "inherit_from:" in text:
            result["warnings"].append(
                "config uses inherit_from; inherited paths were not resolved by this read-only checker"
            )

    estimated = checkpoint / "estimated_c2w.ckpt"
    result["estimated_c2w"] = {
        "path": str(estimated),
        "exists": estimated.is_file(),
        "bytes": estimated.stat().st_size if estimated.is_file() else None,
    }
    if not estimated.is_file():
        result["errors"].append("estimated_c2w.ckpt is missing")
    elif estimated.stat().st_size == 0:
        result["errors"].append("estimated_c2w.ckpt is empty")

    submaps = checkpoint / "submaps"
    result["submaps"] = {"directory": str(submaps), "count": 0, "files": []}
    if not submaps.is_dir():
        result["errors"].append("submaps directory is missing")
    else:
        files = sorted(submaps.glob("*.ckpt"))
        result["submaps"]["count"] = len(files)
        result["submaps"]["files"] = [
            {"name": file.name, "bytes": file.stat().st_size} for file in files
        ]
        if not files:
            result["errors"].append("submaps contains no .ckpt files")
        non_numbered = [file.name for file in files if not re.fullmatch(r"\d+\.ckpt", file.name)]
        if non_numbered:
            result["warnings"].append(
                "submap filenames are not all numeric: " + ", ".join(non_numbered)
            )
        if any(file.stat().st_size == 0 for file in files):
            result["errors"].append("at least one submap checkpoint is empty")

    if result["errors"]:
        result["status"] = "error"
    elif result["warnings"]:
        result["status"] = "warning"
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only file-level checkpoint validator; never loads .ckpt payloads."
    )
    parser.add_argument("--checkpoint", required=True, type=Path)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    result = validate(args.checkpoint, args.config)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"status: {result['status']}")
        print(f"dataset_name: {result.get('dataset_name', '<unknown>')}")
        print(f"scene_name: {result.get('scene_name', '<unknown>')}")
        print(f"submaps: {result['submaps']['count']}")
        for warning in result["warnings"]:
            print(f"warning: {warning}")
        for error in result["errors"]:
            print(f"error: {error}")
        for item in result["unverified"]:
            print(f"unverified: {item}")
    return 0 if result["status"] != "error" else 2


if __name__ == "__main__":
    sys.exit(main())
