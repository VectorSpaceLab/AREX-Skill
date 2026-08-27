#!/usr/bin/env python3
"""Inspect an AnyDoor-style datasets.yaml file without loading datasets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception as exc:  # pragma: no cover - optional in tiny environments
    raise SystemExit(f"PyYAML is required for this helper: {exc}")


KNOWN_FAMILIES = [
    "YoutubeVOS",
    "YoutubeVIS",
    "VIPSeg",
    "UVO",
    "Mose",
    "MVImageNet",
    "VitonHD",
    "Dresscode",
    "FashionTryon",
    "Lvis",
    "SAM",
    "Saliency",
]


def collect_placeholders(node: Any, prefix: str = "") -> list[str]:
    hits: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            child = f"{prefix}.{key}" if prefix else str(key)
            hits.extend(collect_placeholders(value, child))
    elif isinstance(node, list):
        for idx, value in enumerate(node):
            hits.extend(collect_placeholders(value, f"{prefix}[{idx}]") )
    elif isinstance(node, str) and node.startswith("path/"):
        hits.append(f"{prefix}={node}")
    return hits


def summarize_section(section: dict[str, Any]) -> dict[str, Any]:
    return {
        "keys": sorted(section.keys()),
        "placeholders": collect_placeholders(section),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check AnyDoor dataset YAML structure.")
    parser.add_argument("--config", type=Path, required=True, help="Path to datasets.yaml.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable text.")
    args = parser.parse_args()

    data = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    report = {
        "config": str(args.config),
        "top_level_keys": sorted(data.keys()),
        "train": {},
        "test": {},
    }
    for split in ["Train", "Test"]:
        section = data.get(split, {}) or {}
        for name, value in section.items():
            report[split.lower()][name] = summarize_section(value if isinstance(value, dict) else {"value": value})

    report["placeholder_sections"] = collect_placeholders(data)
    report["known_families_present"] = [name for name in KNOWN_FAMILIES if name in (data.get("Train", {}) or {}) or name in (data.get("Test", {}) or {})]

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"config: {report['config']}")
        print(f"top-level keys: {report['top_level_keys']}")
        print(f"known families present: {report['known_families_present']}")
        print("placeholder entries:")
        for item in report["placeholder_sections"]:
            print(f"  {item}")
        for split in ["train", "test"]:
            print(split + ":")
            for name, section in report[split].items():
                print(f"  {name}: keys={section['keys']}")
                if section["placeholders"]:
                    print(f"    placeholders={section['placeholders']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
