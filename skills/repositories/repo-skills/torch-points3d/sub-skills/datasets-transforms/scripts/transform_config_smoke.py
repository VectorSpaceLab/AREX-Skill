#!/usr/bin/env python3
"""Validate Torch Points3D OmegaConf-style data and transform configs safely.

This helper checks dataset class lookup and transform instantiation without
creating datasets, downloading data, preprocessing files, or training.

Examples:
  python sub-skills/datasets-transforms/scripts/transform_config_smoke.py \
    --transforms-yaml '[{"transform":"GridSampling3D","params":{"size":0.1}}]'
  python sub-skills/datasets-transforms/scripts/transform_config_smoke.py \
    --data-config conf/data/segmentation/shapenet.yaml --expect-class ShapeNetDataset
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _as_jsonable(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (list, tuple)):
        return [_as_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _as_jsonable(v) for k, v in value.items()}
    return str(value)


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-check Torch Points3D dataset config and transform resolution.")
    parser.add_argument("--data-config", type=Path, help="Path to a Torch Points3D data YAML to resolve with get_dataset_class.")
    parser.add_argument("--expect-class", help="Optional expected dataset class name, such as ShapeNetDataset.")
    parser.add_argument("--transforms-yaml", help="Inline YAML/JSON transform dict or list to instantiate.")
    parser.add_argument("--json", action="store_true", help="Emit JSON summary.")
    args = parser.parse_args()

    if not args.data_config and not args.transforms_yaml:
        parser.error("provide --data-config and/or --transforms-yaml")

    try:
        from omegaconf import OmegaConf
        from omegaconf.listconfig import ListConfig
        from torch_points3d.core.data_transform import instantiate_transform, instantiate_transforms
        from torch_points3d.datasets.dataset_factory import get_dataset_class
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(f"Import failed; install Torch Points3D, Hydra/OmegaConf, and PyG dependencies first: {type(exc).__name__}: {exc}")

    result = {"data_config": None, "transforms": None, "status": "passed"}

    if args.data_config:
        if not args.data_config.is_file():
            raise SystemExit(f"data config does not exist: {args.data_config}")
        cfg = OmegaConf.load(args.data_config)
        # Some configs inherit task/dataroot through Hydra defaults. This helper
        # only checks direct, already-resolved class lookup unless overrides are
        # present in the file itself.
        try:
            dataset_cls = get_dataset_class(cfg)
        except Exception as exc:  # noqa: BLE001
            raise SystemExit(
                "dataset class resolution failed; check data config task/class/dataroot fields. "
                f"Torch Points3D error: {type(exc).__name__}: {exc}"
            )
        if args.expect_class and dataset_cls.__name__ != args.expect_class:
            raise SystemExit(f"resolved {dataset_cls.__name__}, expected {args.expect_class}")
        result["data_config"] = {
            "path": str(args.data_config),
            "task": _as_jsonable(cfg.get("task")),
            "class": _as_jsonable(cfg.get("class")),
            "resolved_class": dataset_cls.__name__,
        }

    if args.transforms_yaml:
        cfg = OmegaConf.create(args.transforms_yaml)
        try:
            if isinstance(cfg, ListConfig):
                transform = instantiate_transforms(cfg)
                names = [type(t).__name__ for t in transform.transforms]
            else:
                transform = instantiate_transform(cfg)
                names = [type(transform).__name__]
        except Exception as exc:  # noqa: BLE001
            raise SystemExit(
                "transform instantiation failed; check exact transform names and params. "
                f"Torch Points3D error: {type(exc).__name__}: {exc}"
            )
        result["transforms"] = {"classes": names}

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("Torch Points3D config/transform smoke passed")
        if result["data_config"]:
            print("data_config:", result["data_config"])
        if result["transforms"]:
            print("transforms:", ", ".join(result["transforms"]["classes"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
