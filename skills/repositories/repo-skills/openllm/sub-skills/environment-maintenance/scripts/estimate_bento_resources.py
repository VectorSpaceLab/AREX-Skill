#!/usr/bin/env python3
"""Estimate whether an OpenLLM Bento resource spec fits a target.

Examples:
  python estimate_bento_resources.py --bento-yaml ./bento.yaml --target-platform linux
  python estimate_bento_resources.py --resource-json '{"gpu":1,"gpu_type":"nvidia-tesla-l4"}' --gpu NVIDIA-A100:40 --json

This helper is a dry-run estimator. It reads a local YAML/JSON resource spec and
does not start a model, install dependencies, or contact cloud services.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception:  # pragma: no cover - exercised manually
    yaml = None  # type: ignore


ACCELERATOR_SPECS = {
    "nvidia-gtx-1650": ("GTX 1650", 4.0),
    "nvidia-gtx-1060": ("GTX 1060", 6.0),
    "nvidia-gtx-1080-ti": ("GTX 1080 Ti", 11.0),
    "nvidia-rtx-3060": ("RTX 3060", 12.0),
    "nvidia-rtx-3060-ti": ("RTX 3060 Ti", 8.0),
    "nvidia-rtx-3070-ti": ("RTX 3070 Ti", 8.0),
    "nvidia-rtx-3080": ("RTX 3080", 10.0),
    "nvidia-rtx-3080-ti": ("RTX 3080 Ti", 12.0),
    "nvidia-rtx-3090": ("RTX 3090", 24.0),
    "nvidia-rtx-4070-ti": ("RTX 4070 Ti", 12.0),
    "nvidia-tesla-p4": ("P4", 8.0),
    "nvidia-tesla-p100": ("P100", 16.0),
    "nvidia-tesla-k80": ("K80", 12.0),
    "nvidia-tesla-t4": ("T4", 16.0),
    "nvidia-tesla-v100": ("V100", 16.0),
    "nvidia-l4": ("L4", 24.0),
    "nvidia-tesla-l4": ("L4", 24.0),
    "nvidia-tesla-a10g": ("A10G", 24.0),
    "nvidia-a100-80g": ("A100", 80.0),
    "nvidia-a100-80gb": ("A100", 80.0),
    "nvidia-tesla-a100": ("A100", 40.0),
    "nvidia-tesla-h100": ("H100", 80.0),
    "nvidia-h200-141gb": ("H200", 141.0),
    "nvidia-blackwell-b100": ("B100", 192.0),
    "nvidia-blackwell-gb200": ("GB200", 192.0),
}


@dataclass
class Estimate:
    resource: dict[str, Any]
    target_platform: str
    target_gpus: list[dict[str, Any]]
    score: float
    runnable: bool
    notes: list[str]


def parse_memory(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    match = re.match(r"(\d+(?:\.\d+)?)\s*Gi", str(value), re.I)
    if match:
        return float(match.group(1))
    try:
        return float(value)
    except ValueError:
        return 0.0


def load_resource(args: argparse.Namespace) -> dict[str, Any]:
    if args.resource_json:
        return json.loads(args.resource_json)
    if not args.bento_yaml:
        return {}
    if yaml is None:
        raise RuntimeError("PyYAML is required to read --bento-yaml")
    data = yaml.safe_load(args.bento_yaml.read_text()) or {}
    services = data.get("services") or []
    if not services:
        return {}
    config = services[0].get("config") or {}
    return config.get("resources") or {}


def parse_gpu(text: str) -> dict[str, Any]:
    if ":" in text:
        model, memory = text.rsplit(":", 1)
        return {"model": model, "memory_size": float(memory)}
    if text in ACCELERATOR_SPECS:
        model, memory = ACCELERATOR_SPECS[text]
        return {"model": model, "memory_size": memory}
    raise argparse.ArgumentTypeError("GPU must be NAME:GB or a known OpenLLM gpu_type key")


def estimate(resource: dict[str, Any], target_platform: str, target_gpus: list[dict[str, Any]]) -> Estimate:
    notes: list[str] = []
    platforms = str(resource.get("platforms", target_platform)).split(",")
    if target_platform not in platforms:
        return Estimate(resource, target_platform, target_gpus, 0.0, False, ["platform mismatch"])

    gpu_count = int(resource.get("gpu") or 0)
    gpu_type = resource.get("gpu_type") or ""
    parse_memory(resource.get("memory"))  # normalize/check even when not used for score

    if not resource or (gpu_count == 0 and not gpu_type):
        return Estimate(resource, target_platform, target_gpus, 0.5, True, ["no explicit GPU requirement"])

    if gpu_count > 0:
        if gpu_type not in ACCELERATOR_SPECS:
            return Estimate(resource, target_platform, target_gpus, 0.0, False, [f"unknown gpu_type {gpu_type!r}"])
        required_model, required_memory = ACCELERATOR_SPECS[gpu_type]
        compatible = [g for g in target_gpus if float(g["memory_size"]) >= required_memory]
        if len(compatible) < gpu_count:
            return Estimate(resource, target_platform, target_gpus, 0.0, False, [f"requires {gpu_count} x {required_model} with at least {required_memory} GB"])
        total_memory = sum(float(g["memory_size"]) for g in target_gpus) or required_memory * gpu_count
        score = required_memory * gpu_count / total_memory
        return Estimate(resource, target_platform, target_gpus, score, True, ["GPU memory/count requirement fits"])

    return Estimate(resource, target_platform, target_gpus, 1.0, True, ["CPU-compatible resource spec"])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--bento-yaml", type=Path, help="Path to a Bento bento.yaml file.")
    source.add_argument("--resource-json", help="Inline JSON object with resource fields.")
    parser.add_argument("--target-platform", default="linux", help="Target platform name.")
    parser.add_argument("--gpu", action="append", default=[], type=parse_gpu, help="Target GPU as NAME:GB or OpenLLM gpu_type key. May be repeated.")
    parser.add_argument("--json", action="store_true", help="Render JSON output.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        result = estimate(load_resource(args), args.target_platform, args.gpu)
    except Exception as exc:
        print(f"resource estimate failed: {exc.__class__.__name__}: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(asdict(result), indent=2, sort_keys=False))
    else:
        print(f"runnable: {result.runnable}")
        print(f"score: {result.score}")
        for note in result.notes:
            print(f"note: {note}")
    return 0 if result.runnable else 2


if __name__ == "__main__":
    raise SystemExit(main())
