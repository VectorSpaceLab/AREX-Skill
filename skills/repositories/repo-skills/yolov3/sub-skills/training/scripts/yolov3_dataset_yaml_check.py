#!/usr/bin/env python3
"""Validate YOLOv3 dataset YAML structure without downloading data."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml


def as_names(value):
    if isinstance(value, dict):
        return [value[k] for k in sorted(value, key=lambda x: int(x) if str(x).isdigit() else str(x))]
    if isinstance(value, list):
        return value
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Check required fields and path resolution for a YOLOv3 dataset YAML.")
    parser.add_argument("yaml_path")
    parser.add_argument("--repo-root", default=".", help="base used when YAML path is relative")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    repo_root = Path(args.repo_root).resolve()
    yaml_path = Path(args.yaml_path)
    yaml_path = yaml_path if yaml_path.is_absolute() else repo_root / yaml_path
    result = {"yaml": str(yaml_path), "errors": [], "warnings": [], "resolved": {}}
    if not yaml_path.exists():
        result["errors"].append("YAML file does not exist")
    else:
        data = yaml.safe_load(yaml_path.read_text()) or {}
        for key in ("train", "val", "names"):
            if key not in data:
                result["errors"].append(f"missing required key: {key}")
        names = as_names(data.get("names"))
        if names is None:
            result["errors"].append("names must be a list or index-to-name mapping")
        else:
            result["derived_nc"] = len(names)
            if "nc" in data and int(data["nc"]) != len(names):
                result["errors"].append(f"nc={data['nc']} but names has {len(names)} entries")
        base = Path(data.get("path") or ".")
        if not base.is_absolute():
            base = (repo_root / base).resolve()
        result["resolved"]["path"] = str(base)
        for key in ("train", "val", "test"):
            if data.get(key):
                value = data[key]
                paths = value if isinstance(value, list) else [value]
                resolved = []
                for item in paths:
                    p = Path(str(item))
                    if not p.is_absolute():
                        p = base / p
                    resolved.append({"path": str(p), "exists": p.exists()})
                result["resolved"][key] = resolved
                if key in ("train", "val") and not any(x["exists"] for x in resolved):
                    result["warnings"].append(f"no existing paths found for {key}")
        if "download" in data:
            result["warnings"].append("download key is present; do not execute it without approval")
    result["status"] = "FAIL" if result["errors"] else "WARN" if result["warnings"] else "PASS"
    print(json.dumps(result, indent=2) if args.json else result)
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
