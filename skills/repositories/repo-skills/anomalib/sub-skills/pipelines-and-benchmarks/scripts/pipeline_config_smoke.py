#!/usr/bin/env python3
"""Lightweight import and config smoke checks for Anomalib pipelines.

This helper is intentionally read-only. It imports public pipeline entrypoints,
validates YAML shape, counts benchmark grids, estimates tiled-ensemble tile
counts, and checks an optional evaluation root. It does not call Pipeline.run,
train models, evaluate models, download data, or create result directories.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


class SmokeError(RuntimeError):
    """Configuration failed a smoke check."""


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except Exception as exc:  # pragma: no cover - depends on caller env
        raise SmokeError("PyYAML is required to read pipeline YAML configs") from exc

    if not path.exists():
        raise SmokeError(f"config does not exist: {path}")
    if not path.is_file():
        raise SmokeError(f"config is not a file: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise SmokeError(f"config must parse to a mapping: {path}")
    return data


def _import_entrypoints() -> dict[str, str]:
    try:
        from anomalib.pipelines import Benchmark
        from anomalib.pipelines.tiled_ensemble import EvalTiledEnsemble, TrainTiledEnsemble
    except Exception as exc:  # pragma: no cover - depends on caller env
        raise SmokeError(f"failed to import Anomalib pipeline entrypoints: {exc}") from exc

    return {
        "Benchmark": f"{Benchmark.__module__}.{Benchmark.__name__}",
        "TrainTiledEnsemble": f"{TrainTiledEnsemble.__module__}.{TrainTiledEnsemble.__name__}",
        "EvalTiledEnsemble": f"{EvalTiledEnsemble.__module__}.{EvalTiledEnsemble.__name__}",
    }


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else [value]


def _count_grids(node: Any, path: str = "") -> tuple[int, list[str], list[str]]:
    """Return product count, grid paths, and warnings for grid-like keys."""
    product_count = 1
    grid_paths: list[str] = []
    warnings: list[str] = []

    if isinstance(node, dict):
        for key, value in node.items():
            child_path = f"{path}.{key}" if path else str(key)
            if key == "grid":
                if not isinstance(value, list):
                    warnings.append(f"{child_path} should be a list")
                else:
                    product_count *= max(len(value), 0)
                    grid_paths.append(child_path)
            elif "grid" in str(key):
                warnings.append(f"{child_path} is grid-like; current tested configs use the exact key 'grid'")
                child_count, child_paths, child_warnings = _count_grids(value, child_path)
                product_count *= child_count
                grid_paths.extend(child_paths)
                warnings.extend(child_warnings)
            else:
                child_count, child_paths, child_warnings = _count_grids(value, child_path)
                product_count *= child_count
                grid_paths.extend(child_paths)
                warnings.extend(child_warnings)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            child_count, child_paths, child_warnings = _count_grids(value, f"{path}[{index}]")
            product_count *= child_count
            grid_paths.extend(child_paths)
            warnings.extend(child_warnings)

    return product_count, grid_paths, warnings


def _cuda_device_count() -> int | None:
    try:
        import torch
    except Exception:
        return None
    try:
        return int(torch.cuda.device_count())
    except Exception:
        return None


def _validate_benchmark_config(config: dict[str, Any]) -> dict[str, Any]:
    if "accelerator" not in config:
        raise SmokeError("benchmark config is missing top-level 'accelerator'")
    if "benchmark" not in config or not isinstance(config["benchmark"], dict):
        raise SmokeError("benchmark config is missing mapping section 'benchmark'")

    accelerators = _as_list(config["accelerator"])
    unsupported = [item for item in accelerators if item not in {"cpu", "cuda"}]
    if unsupported:
        raise SmokeError(f"unsupported benchmark accelerator(s): {unsupported}; use 'cpu' or 'cuda'")

    grid_count, grid_paths, warnings = _count_grids(config["benchmark"])
    if not grid_paths:
        warnings.append("no benchmark grid leaves found; this config will generate one benchmark job per accelerator")

    cuda_count = _cuda_device_count()
    runner_plan = []
    for accelerator in accelerators:
        if accelerator == "cpu":
            runner_plan.append({"accelerator": "cpu", "runner": "SerialRunner", "n_jobs": 1})
        elif cuda_count is None:
            runner_plan.append({"accelerator": "cuda", "runner": "unknown", "n_jobs": None})
            warnings.append("could not inspect torch.cuda.device_count(); verify CUDA before execution")
        elif cuda_count > 1:
            runner_plan.append({"accelerator": "cuda", "runner": "ParallelRunner", "n_jobs": cuda_count})
        else:
            runner_plan.append({"accelerator": "cuda", "runner": "SerialRunner", "n_jobs": 1})
            if cuda_count == 0:
                warnings.append("CUDA accelerator requested but no CUDA devices are visible; switch to cpu for CPU-only execution")

    return {
        "grid_count_per_accelerator": grid_count,
        "grid_paths": grid_paths,
        "accelerators": accelerators,
        "runner_plan": runner_plan,
        "warnings": warnings,
    }


def _pair(value: Any, field: str) -> tuple[int, int]:
    if isinstance(value, int):
        if value <= 0:
            raise SmokeError(f"{field} must be positive")
        return value, value
    if isinstance(value, (list, tuple)) and len(value) == 2 and all(isinstance(item, int) for item in value):
        if value[0] <= 0 or value[1] <= 0:
            raise SmokeError(f"{field} values must be positive")
        return int(value[0]), int(value[1])
    raise SmokeError(f"{field} must be a positive int or a two-int list")


def _estimate_tile_grid(tiling: dict[str, Any]) -> dict[str, Any]:
    image_h, image_w = _pair(tiling.get("image_size"), "tiling.image_size")
    tile_h, tile_w = _pair(tiling.get("tile_size"), "tiling.tile_size")
    stride_h, stride_w = _pair(tiling.get("stride"), "tiling.stride")
    if tile_h > image_h or tile_w > image_w:
        raise SmokeError("tiling.tile_size should not exceed tiling.image_size for a smoke configuration")

    num_h = max(1, math.ceil((image_h - tile_h) / stride_h) + 1)
    num_w = max(1, math.ceil((image_w - tile_w) / stride_w) + 1)
    return {
        "image_size": [image_h, image_w],
        "tile_size": [tile_h, tile_w],
        "stride": [stride_h, stride_w],
        "grid": [num_h, num_w],
        "tile_jobs": num_h * num_w,
        "overlap": stride_h < tile_h or stride_w < tile_w,
    }


def _validate_tiled_config(config: dict[str, Any]) -> dict[str, Any]:
    required = [
        "seed",
        "accelerator",
        "default_root_dir",
        "tiling",
        "normalization_stage",
        "thresholding_stage",
        "data",
        "SeamSmoothing",
        "TrainModels",
    ]
    missing = [key for key in required if key not in config]
    if missing:
        raise SmokeError(f"tiled ensemble config is missing top-level section(s): {missing}")

    warnings: list[str] = []
    accelerator = config["accelerator"]
    if accelerator not in {"cpu", "cuda"}:
        warnings.append("tiled ensemble has only been smoke-planned here for accelerator 'cpu' or 'cuda'")

    if config["normalization_stage"] not in {"tile", "image", "none"}:
        raise SmokeError("normalization_stage must be one of: tile, image, none")
    if config["thresholding_stage"] not in {"tile", "image"}:
        raise SmokeError("thresholding_stage must be one of: tile, image")

    if not isinstance(config["tiling"], dict):
        raise SmokeError("tiling must be a mapping")
    tile_summary = _estimate_tile_grid(config["tiling"])

    data = config["data"]
    if not isinstance(data, dict) or "class_path" not in data or "init_args" not in data:
        raise SmokeError("data must contain class_path and init_args")
    if not isinstance(data["init_args"], dict):
        raise SmokeError("data.init_args must be a mapping")
    if "root" not in data["init_args"]:
        warnings.append("data.init_args.root is missing; execution will need a dataset root")

    smoothing = config["SeamSmoothing"]
    if not isinstance(smoothing, dict) or "apply" not in smoothing:
        raise SmokeError("SeamSmoothing must contain apply")

    train_models = config["TrainModels"]
    if not isinstance(train_models, dict) or "model" not in train_models:
        raise SmokeError("TrainModels must contain model")
    if not isinstance(train_models["model"], dict) or "class_path" not in train_models["model"]:
        raise SmokeError("TrainModels.model must contain class_path")

    if accelerator == "cuda":
        cuda_count = _cuda_device_count()
        if cuda_count == 0:
            warnings.append("CUDA requested but no CUDA devices are visible; use cpu for CPU-only smoke execution")
        elif cuda_count is None:
            warnings.append("could not inspect CUDA device count; verify hardware before execution")

    return {
        "accelerator": accelerator,
        "tile_summary": tile_summary,
        "normalization_stage": config["normalization_stage"],
        "thresholding_stage": config["thresholding_stage"],
        "seam_smoothing": bool(smoothing["apply"]),
        "warnings": warnings,
    }


def _check_eval_root(root: Path, tile_summary: dict[str, Any] | None) -> dict[str, Any]:
    if not root.exists():
        raise SmokeError(f"eval root does not exist: {root}")
    if not root.is_dir():
        raise SmokeError(f"eval root is not a directory: {root}")

    weights = root / "weights" / "lightning"
    warnings: list[str] = []
    if not weights.is_dir():
        warnings.append("eval root does not contain weights/lightning; it may be a parent results directory or dataset root")
        checkpoints: list[str] = []
    else:
        checkpoints = sorted(path.name for path in weights.glob("model*_*.ckpt"))
        if tile_summary is not None:
            expected = tile_summary["tile_jobs"]
            if len(checkpoints) < expected:
                warnings.append(f"found {len(checkpoints)} tiled checkpoints but estimated {expected} tile jobs")
        if not (weights / "stats.json").exists():
            warnings.append("weights/lightning/stats.json is missing; image-level stats may be unavailable")

    return {
        "root": str(root),
        "weights_lightning_exists": weights.is_dir(),
        "checkpoint_count": len(checkpoints),
        "checkpoint_names": checkpoints[:12],
        "warnings": warnings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--import-only", action="store_true", help="Only verify public pipeline imports")
    parser.add_argument("--benchmark-config", type=Path, help="Benchmark YAML config to inspect")
    parser.add_argument("--tiled-config", type=Path, help="Tiled ensemble YAML config to inspect")
    parser.add_argument("--eval-root", type=Path, help="Optional tiled ensemble evaluation root to check")
    parser.add_argument("--json", action="store_true", help="Emit compact JSON only")
    args = parser.parse_args(argv)

    report: dict[str, Any] = {"imports": _import_entrypoints()}
    tiled_summary: dict[str, Any] | None = None

    if args.benchmark_config is not None:
        report["benchmark"] = _validate_benchmark_config(_load_yaml(args.benchmark_config))
    if args.tiled_config is not None:
        tiled_summary = _validate_tiled_config(_load_yaml(args.tiled_config))
        report["tiled_ensemble"] = tiled_summary
    if args.eval_root is not None:
        report["eval_root"] = _check_eval_root(args.eval_root, tiled_summary.get("tile_summary") if tiled_summary else None)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("Anomalib pipeline smoke check passed.")
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SmokeError as exc:
        print(f"pipeline smoke check failed: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
