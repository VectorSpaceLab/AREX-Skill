#!/usr/bin/env python3
"""Validate Lumina image-training manifests and config layout.

This helper checks the JourneyDB-style YAML plus the referenced JSON/JSONL
manifests without starting a training job.

Examples:
    python check_training_data.py --config lumina_t2i/configs/data/JourneyDB.yaml
    python check_training_data.py --config /path/to/config.yaml --max-items 3
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml


def load_manifest(path: Path) -> list[dict]:
    if path.suffix == ".json":
        with path.open() as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError(f"{path} must contain a JSON list")
        return data
    if path.suffix == ".jsonl":
        rows = []
        with path.open() as f:
            for line_no, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise ValueError(f"{path}:{line_no}: invalid JSONL row") from exc
        return rows
    raise ValueError(f"unsupported manifest extension: {path.suffix}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--max-items", type=int, default=3)
    args = parser.parse_args()

    config_path = args.config.resolve()
    print(f"config={config_path}")
    if not config_path.exists():
        print("FAIL: config file does not exist")
        return 1

    with config_path.open() as f:
        config = yaml.safe_load(f)
    if not isinstance(config, dict) or "META" not in config:
        print("FAIL: config must contain a META list")
        return 1

    ok = True
    for idx, meta in enumerate(config["META"]):
        print(f"\n[META {idx}]")
        if not isinstance(meta, dict):
            print("FAIL: each META entry must be a mapping")
            ok = False
            continue
        manifest_path = Path(meta["path"])
        if not manifest_path.is_absolute():
            manifest_path = (config_path.parent / manifest_path).resolve()
        root = meta.get("root")
        if root is not None:
            root = Path(root)
            if not root.is_absolute():
                root = (config_path.parent / root).resolve()
        print(f"manifest={manifest_path}")
        if root is not None:
            print(f"root={root}")
        if not manifest_path.exists():
            print("FAIL: manifest file does not exist")
            ok = False
            continue

        try:
            rows = load_manifest(manifest_path)
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL: could not read manifest ({type(exc).__name__}: {exc})")
            ok = False
            continue

        print(f"rows={len(rows)}")
        if not rows:
            print("FAIL: manifest is empty")
            ok = False
            continue

        sample_rows = rows[: args.max_items]
        for row_idx, row in enumerate(sample_rows):
            if not isinstance(row, dict):
                print(f"FAIL: row {row_idx} is not a mapping")
                ok = False
                continue
            if "conversations" not in row or "image" not in row:
                print(f"FAIL: row {row_idx} missing conversations/image")
                ok = False
                continue
            conversations = row["conversations"]
            if not isinstance(conversations, list) or len(conversations) < 2:
                print(f"FAIL: row {row_idx} has an invalid conversations list")
                ok = False
            image_path = Path(row["image"])
            if root is not None and not image_path.is_absolute():
                image_path = (root / image_path).resolve()
            print(f"  sample[{row_idx}] image={image_path}")
            if root is not None and not image_path.exists():
                print(f"  FAIL: sample[{row_idx}] image path does not exist")
                ok = False

    if ok:
        print("\nResult: training data layout looks valid.")
        return 0

    print("\nResult: training data layout has problems.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
