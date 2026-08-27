#!/usr/bin/env python3
"""Summarize a PaddleDetection PP-Human/PP-Vehicle pipeline YAML."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize PaddleDetection pipeline config modules and model paths.")
    parser.add_argument("config", help="Pipeline YAML config.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    path = Path(args.config)
    if not path.exists():
        parser.error(f"config not found: {path}")
    data = yaml.safe_load(path.read_text()) or {}
    modules = []
    for key, value in data.items():
        if isinstance(value, dict):
            enabled = value.get("enable", True)
            model_fields = {k: v for k, v in value.items() if "model" in k.lower() or k.endswith("_dir")}
            modules.append({"name": key, "enabled": enabled, "model_fields": model_fields})
    summary = {
        "config": str(path),
        "visual": data.get("visual"),
        "modules": modules,
        "module_count": len(modules),
    }
    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print(f"config: {path}")
        print(f"visual: {data.get('visual')}")
        for item in modules:
            print(f"{item['name']}: enabled={item['enabled']} models={item['model_fields']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
