#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from typing import Any

from boxmot.configs import list_training_recipes
from boxmot.reid.backbones import registered_backbone_names
from boxmot.reid.core.config import NR_CLASSES_DICT, REID_EXPORT_FORMATS, TRAINED_URLS
from boxmot.reid.datasets import DATASET_REGISTRY


def _limit_items(items: list[str], limit: int) -> list[str]:
    return items[: max(0, int(limit))]


def _export_formats() -> list[dict[str, Any]]:
    return [
        {
            "name": item.name,
            "argument": item.argument,
            "suffix": item.suffix,
            "cpu": bool(item.cpu),
            "gpu": bool(item.gpu),
        }
        for item in REID_EXPORT_FORMATS
    ]


def _dataset_aliases() -> dict[str, list[str]]:
    groups: dict[str, list[str]] = defaultdict(list)
    for alias, dataset_cls in DATASET_REGISTRY.items():
        groups[dataset_cls.__name__].append(alias)
    return {name: sorted(aliases) for name, aliases in sorted(groups.items())}


def build_summary(limit: int = 5) -> dict[str, Any]:
    backbone_names = list(registered_backbone_names())
    recipe_names = list(list_training_recipes())
    trained_url_keys = sorted(TRAINED_URLS)
    dataset_registry_keys = sorted(DATASET_REGISTRY)

    return {
        "backbones": {
            "count": len(backbone_names),
            "examples": _limit_items(backbone_names, limit),
        },
        "training_recipes": {
            "count": len(recipe_names),
            "examples": _limit_items(recipe_names, limit),
        },
        "export_formats": _export_formats(),
        "trained_urls": {
            "count": len(trained_url_keys),
            "examples": _limit_items(trained_url_keys, limit),
        },
        "dataset_registry_keys": dataset_registry_keys,
        "dataset_aliases": _dataset_aliases(),
        "dataset_class_aliases": dict(sorted(NR_CLASSES_DICT.items())),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize BoxMOT ReID registries safely.")
    parser.add_argument("--limit", type=int, default=5, help="Maximum number of examples to print per section")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of text")
    args = parser.parse_args()

    summary = build_summary(args.limit)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"backbones ({summary['backbones']['count']}): {', '.join(summary['backbones']['examples'])}")
        print(
            f"training recipes ({summary['training_recipes']['count']}): "
            f"{', '.join(summary['training_recipes']['examples'])}"
        )
        print(f"export formats: {[item['name'] for item in summary['export_formats']]}")
        print(f"trained urls ({summary['trained_urls']['count']}): {', '.join(summary['trained_urls']['examples'])}")
        print(f"dataset registry keys: {', '.join(summary['dataset_registry_keys'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
