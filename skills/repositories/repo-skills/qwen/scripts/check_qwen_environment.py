#!/usr/bin/env python3
"""Safely inspect Qwen-related dependencies and local checkpoint shape.

This helper never downloads a model, loads checkpoint weights, starts a service,
invokes Docker, or contacts a hosted API. Use it before selecting a heavier
Qwen workflow.
"""
from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
from pathlib import Path
from typing import Any

DEFAULT_MODULES = ("torch", "transformers", "tiktoken", "accelerate", "einops")

def _checkpoint(path: str) -> dict[str, Any]:
    p = Path(path).expanduser()
    result: dict[str, Any] = {"path": str(p), "exists": p.exists(), "is_dir": p.is_dir()}
    if not p.is_dir():
        return result
    files = {x.name for x in p.iterdir() if x.is_file()}
    result["has_config"] = "config.json" in files
    result["has_tokenizer"] = any(x in files for x in ("tokenizer_config.json", "tokenizer.json", "qwen.tiktoken"))
    result["shard_count"] = len([x for x in files if x.startswith("pytorch_model-") or x.startswith("model-")])
    result["warnings"] = []
    if not result["has_config"]:
        result["warnings"].append("config.json is missing")
    if not result["has_tokenizer"]:
        result["warnings"].append("no common tokenizer marker found")
    return result

def main() -> int:
    parser = argparse.ArgumentParser(description="Check Qwen dependencies, optional CUDA, and local checkpoint shape without loading models.")
    parser.add_argument("--check-dependencies", action="store_true", help="Import common modules and report distribution versions.")
    parser.add_argument("--check-cuda", action="store_true", help="If torch is installed, report CUDA visibility and device names; allocate nothing.")
    parser.add_argument("--checkpoint", type=str, help="Inspect a local checkpoint directory without downloading or loading it.")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Emit one JSON object instead of human-readable lines.")
    args = parser.parse_args()
    result: dict[str, Any] = {}
    if args.check_dependencies:
        modules: dict[str, Any] = {}
        for name in DEFAULT_MODULES:
            try:
                importlib.import_module(name)
                try:
                    version = importlib.metadata.version(name)
                except importlib.metadata.PackageNotFoundError:
                    version = None
                modules[name] = {"ok": True, "version": version}
            except Exception as exc:  # import diagnostics should not hide the module name
                modules[name] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
        result["dependencies"] = modules
    if args.check_cuda:
        try:
            torch = importlib.import_module("torch")
            result["cuda"] = {"available": bool(torch.cuda.is_available()), "count": int(torch.cuda.device_count())}
            if torch.cuda.is_available():
                result["cuda"]["devices"] = [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())]
        except Exception as exc:
            result["cuda"] = {"available": False, "error": f"{type(exc).__name__}: {exc}"}
    if args.checkpoint:
        result["checkpoint"] = _checkpoint(args.checkpoint)
    if not result:
        result["hint"] = "Select --check-dependencies, --check-cuda, or --checkpoint."
    if args.as_json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for key, value in result.items():
            print(f"{key}: {json.dumps(value, sort_keys=True)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
