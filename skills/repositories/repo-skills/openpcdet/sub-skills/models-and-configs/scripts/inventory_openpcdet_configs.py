#!/usr/bin/env python3
"""Inventory OpenPCDet YAML configs and detector/dataset names."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return data


def get_nested(data: dict[str, Any], *keys: str) -> Any:
    cur: Any = data
    for key in keys:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


def main() -> int:
    parser = argparse.ArgumentParser(description="Inventory OpenPCDet configs")
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="OpenPCDet checkout root")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    repo = args.repo.resolve()
    cfg_root = repo / "tools" / "cfgs"
    if not cfg_root.is_dir():
        raise SystemExit(f"No tools/cfgs directory found under {repo}")

    sys.path.insert(0, str(repo))
    registry: dict[str, Any] = {}
    try:
        import pcdet.datasets as datasets
        import pcdet.models.detectors as detectors

        registry = {
            "datasets": sorted(datasets.__all__.keys()),
            "detectors": sorted(k for k in detectors.__all__.keys() if k != "Detector3DTemplate"),
        }
    except Exception as exc:  # noqa: BLE001 - diagnostic inventory
        registry = {"error_type": type(exc).__name__, "error": str(exc)}

    configs = []
    for path in sorted(cfg_root.rglob("*.yaml")):
        data = load_yaml(path)
        configs.append(
            {
                "path": str(path.relative_to(repo)),
                "group": path.parent.name,
                "dataset": get_nested(data, "DATA_CONFIG", "DATASET"),
                "model": get_nested(data, "MODEL", "NAME"),
                "classes": data.get("CLASS_NAMES"),
                "batch_size_per_gpu": get_nested(data, "OPTIMIZATION", "BATCH_SIZE_PER_GPU"),
                "num_epochs": get_nested(data, "OPTIMIZATION", "NUM_EPOCHS"),
            }
        )

    report = {"registry": registry, "config_count": len(configs), "configs": configs}
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("Registry:")
        for key, value in registry.items():
            print(f"- {key}: {value}")
        print(f"\nConfigs: {len(configs)}")
        for cfg in configs:
            print(
                "- {path}: dataset={dataset} model={model} classes={classes} batch={batch} epochs={epochs}".format(
                    path=cfg["path"],
                    dataset=cfg["dataset"],
                    model=cfg["model"],
                    classes=cfg["classes"],
                    batch=cfg["batch_size_per_gpu"],
                    epochs=cfg["num_epochs"],
                )
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
