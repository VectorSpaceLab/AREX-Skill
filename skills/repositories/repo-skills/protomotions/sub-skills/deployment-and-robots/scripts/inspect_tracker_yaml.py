#!/usr/bin/env python3
"""Summarize a ProtoMotions deployment YAML sidecar."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


def _find_key(obj: Any, names: set[str]) -> list[Any]:
    found = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            if str(key) in names:
                found.append(value)
            found.extend(_find_key(value, names))
    elif isinstance(obj, list):
        for item in obj:
            found.extend(_find_key(item, names))
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("yaml_path", help="unified_pipeline.yaml sidecar")
    args = parser.parse_args()
    data = yaml.safe_load(Path(args.yaml_path).read_text())
    summary = {
        "top_level_keys": sorted(map(str, data.keys())) if isinstance(data, dict) else [],
        "input_sections": _find_key(data, {"inputs", "onnx_inputs", "input_names"}),
        "output_sections": _find_key(data, {"outputs", "onnx_outputs", "output_names"}),
        "timing_sections": _find_key(data, {"timing", "control"}),
        "robot_sections": _find_key(data, {"robot", "robot_config"}),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
