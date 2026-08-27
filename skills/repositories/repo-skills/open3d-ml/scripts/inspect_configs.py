#!/usr/bin/env python3
"""Inspect Open3D-ML YAML config files without running pipelines."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def read_config(path: Path):
    try:
        import yaml
    except Exception as exc:
        return {"path": str(path), "error": f"PyYAML unavailable: {type(exc).__name__}: {exc}"}
    try:
        data = yaml.safe_load(path.read_text()) or {}
    except Exception as exc:
        return {"path": str(path), "error": f"failed to load YAML: {type(exc).__name__}: {exc}"}
    summary = {"path": str(path), "sections": {}, "error": None}
    for section in ("dataset", "model", "pipeline"):
        value = data.get(section, {}) if isinstance(data, dict) else {}
        if isinstance(value, dict):
            summary["sections"][section] = {"name": value.get("name"), "keys": sorted(value.keys())}
        else:
            summary["sections"][section] = {"name": None, "keys": []}
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description="Summarize Open3D-ML YAML config files.")
    parser.add_argument("paths", nargs="+", help="Config files or directories containing .yml/.yaml files.")
    parser.add_argument("--max-files", type=int, default=100)
    args = parser.parse_args(argv)
    files = []
    for item in args.paths:
        path = Path(item)
        if path.is_dir():
            files.extend(sorted(path.glob("*.yml")))
            files.extend(sorted(path.glob("*.yaml")))
        elif path.exists():
            files.append(path)
    files = files[:args.max_files]
    report = {"files": [read_config(p) for p in files], "count": len(files)}
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
