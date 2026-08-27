#!/usr/bin/env python3
"""Summarize and sanity-check an OpenPCDet YAML config.

This helper mirrors the repository's config loader but does not build datasets,
models, or run CUDA kernels. It is safe for quick routing/debugging.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


def to_plain(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: to_plain(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_plain(v) for v in obj]
    return obj


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize an OpenPCDet config")
    parser.add_argument("--repo", type=Path, default=None, help="Optional OpenPCDet checkout root")
    parser.add_argument("--cfg", type=Path, required=True, help="Config YAML path")
    parser.add_argument("--set", dest="set_cfgs", nargs=argparse.REMAINDER, default=None, help="OpenPCDet cfg overrides")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args()

    cfg_path = args.cfg
    if args.repo is not None:
        repo = args.repo.resolve()
        if not (repo / "pcdet").is_dir():
            raise SystemExit(f"--repo is not an OpenPCDet checkout: {args.repo}")
        sys.path.insert(0, str(repo))
        if not cfg_path.is_absolute():
            cfg_path = (repo / cfg_path).resolve()
        tools_dir = repo / "tools"
        if tools_dir in cfg_path.parents:
            os.chdir(tools_dir)
            cfg_arg = str(cfg_path.relative_to(tools_dir))
        else:
            os.chdir(cfg_path.parent)
            cfg_arg = cfg_path.name
    else:
        cfg_path = cfg_path.resolve()
        if cfg_path.parent.name.endswith("_models") and cfg_path.parent.parent.name == "cfgs":
            tools_dir = cfg_path.parent.parent.parent
            os.chdir(tools_dir)
            cfg_arg = str(cfg_path.relative_to(tools_dir))
        else:
            os.chdir(cfg_path.parent)
            cfg_arg = cfg_path.name

    from pcdet.config import cfg, cfg_from_list, cfg_from_yaml_file

    cfg_from_yaml_file(cfg_arg, cfg)
    if args.set_cfgs:
        cfg_from_list(args.set_cfgs, cfg)

    data_cfg = cfg.get("DATA_CONFIG", {})
    model_cfg = cfg.get("MODEL", {})
    optim_cfg = cfg.get("OPTIMIZATION", {})

    processors = []
    for proc in data_cfg.get("DATA_PROCESSOR", []) or []:
        processors.append(proc.get("NAME", "<unnamed>"))

    augmentors = []
    for aug in (data_cfg.get("DATA_AUGMENTOR", {}) or {}).get("AUG_CONFIG_LIST", []) or []:
        augmentors.append(aug.get("NAME", "<unnamed>"))

    summary = {
        "config": str(args.cfg),
        "classes": list(cfg.get("CLASS_NAMES", [])),
        "dataset": data_cfg.get("DATASET"),
        "data_path": data_cfg.get("DATA_PATH"),
        "point_cloud_range": data_cfg.get("POINT_CLOUD_RANGE"),
        "data_processors": processors,
        "augmentors": augmentors,
        "model_name": model_cfg.get("NAME"),
        "vfe": (model_cfg.get("VFE", {}) or {}).get("NAME"),
        "backbone_3d": (model_cfg.get("BACKBONE_3D", {}) or {}).get("NAME"),
        "map_to_bev": (model_cfg.get("MAP_TO_BEV", {}) or {}).get("NAME"),
        "backbone_2d": (model_cfg.get("BACKBONE_2D", {}) or {}).get("NAME"),
        "dense_head": (model_cfg.get("DENSE_HEAD", {}) or {}).get("NAME"),
        "roi_head": (model_cfg.get("ROI_HEAD", {}) or {}).get("NAME"),
        "batch_size_per_gpu": optim_cfg.get("BATCH_SIZE_PER_GPU"),
        "num_epochs": optim_cfg.get("NUM_EPOCHS"),
        "optimizer": optim_cfg.get("OPTIMIZER"),
        "use_amp": optim_cfg.get("USE_AMP"),
    }

    warnings = []
    if not summary["dataset"]:
        warnings.append("DATA_CONFIG.DATASET is missing")
    if not summary["model_name"]:
        warnings.append("MODEL.NAME is missing")
    if not summary["classes"]:
        warnings.append("CLASS_NAMES is empty")
    pcr = summary["point_cloud_range"]
    if pcr is not None and len(pcr) != 6:
        warnings.append("POINT_CLOUD_RANGE should contain six numbers")
    summary["warnings"] = warnings

    if args.json:
        print(json.dumps(to_plain(summary), indent=2, sort_keys=True))
    else:
        for key, value in summary.items():
            if key == "warnings":
                continue
            print(f"{key}: {value}")
        if warnings:
            print("\nWarnings:")
            for warning in warnings:
                print(f"- {warning}")
    return 1 if warnings else 0


if __name__ == "__main__":
    raise SystemExit(main())
