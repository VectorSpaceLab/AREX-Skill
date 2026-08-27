#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from boxmot.configs.benchmark import load_benchmark_cfg, resolve_benchmark_cfg_path


def _compact_component(component: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(component, dict):
        return None
    keys = (
        "id",
        "model",
        "default_model",
        "url",
        "model_url",
        "preprocess",
        "half",
        "imgsz",
        "conf",
        "device",
        "box_type",
    )
    return {key: component.get(key) for key in keys if key in component}


def build_summary(benchmark: str) -> dict[str, Any]:
    cfg_path = resolve_benchmark_cfg_path(benchmark)
    cfg = load_benchmark_cfg(cfg_path)
    benchmark_cfg = cfg.get("benchmark", {}) if isinstance(cfg, dict) else {}
    dataset_cfg = cfg.get("dataset", {}) if isinstance(cfg, dict) else {}
    detector_cfg = cfg.get("detector", {}) if isinstance(cfg, dict) else {}
    reid_cfg = cfg.get("reid", {}) if isinstance(cfg, dict) else {}
    download_cfg = cfg.get("download", {}) if isinstance(cfg, dict) else {}
    evaluation_cfg = cfg.get("evaluation", {}) if isinstance(cfg, dict) else {}
    storage_cfg = cfg.get("storage", {}) if isinstance(cfg, dict) else {}

    return {
        "benchmark": benchmark_cfg.get("id") or cfg.get("id") or cfg_path.stem,
        "cfg_path": str(cfg_path),
        "dataset": _compact_component(dataset_cfg),
        "detector": _compact_component(detector_cfg),
        "reid": _compact_component(reid_cfg),
        "evaluation": {
            "box_type": evaluation_cfg.get("box_type"),
            "layout": evaluation_cfg.get("layout"),
            "metric_eval": evaluation_cfg.get("metric_eval"),
            "class_bridge_count": len(evaluation_cfg.get("classes", {}).get("bridge", []) or []),
        },
        "storage": storage_cfg,
        "download_keys": sorted(download_cfg.keys()) if isinstance(download_cfg, dict) else [],
        "split_names": sorted((cfg.get("splits") or {}).keys()) if isinstance(cfg.get("splits"), dict) else [],
        "benchmark_keys": sorted(benchmark_cfg.keys()) if isinstance(benchmark_cfg, dict) else [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize a BoxMOT benchmark config safely.")
    parser.add_argument("--benchmark", required=True, help="Benchmark id or YAML path")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of a text summary")
    args = parser.parse_args()

    summary = build_summary(args.benchmark)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"benchmark: {summary['benchmark']}")
        print(f"cfg_path: {summary['cfg_path']}")
        print(f"dataset: {summary['dataset']}")
        print(f"detector: {summary['detector']}")
        print(f"reid: {summary['reid']}")
        print(f"evaluation: {summary['evaluation']}")
        print(f"storage: {summary['storage']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
