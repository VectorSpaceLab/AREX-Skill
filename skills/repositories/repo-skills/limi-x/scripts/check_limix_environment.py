#!/usr/bin/env python3
"""Safe LimiX environment/config diagnostic.

This helper checks imports, optional CUDA availability, and the shape of a LimiX
inference config JSON. It does not download checkpoints or run full model
inference.

Examples:
  python scripts/check_limix_environment.py --config path/to/config.json
  python scripts/check_limix_environment.py --config path/to/config.json --expect-cuda
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import Any


def load_config(path: Path) -> list[dict[str, Any]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - exact JSON errors vary
        raise SystemExit(f"ERROR: could not read config JSON: {exc}") from exc
    if not isinstance(data, list) or not data:
        raise SystemExit("ERROR: config must be a non-empty JSON list of pipeline objects")
    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            raise SystemExit(f"ERROR: pipeline {idx} is not an object")
        if "retrieval_config" not in item or not isinstance(item["retrieval_config"], dict):
            raise SystemExit(f"ERROR: pipeline {idx} is missing object field retrieval_config")
    return data


def try_import(name: str) -> tuple[bool, str]:
    try:
        mod = importlib.import_module(name)
        return True, getattr(mod, "__file__", "built-in/namespace") or "namespace"
    except Exception as exc:  # pragma: no cover - diagnostic output
        return False, f"{type(exc).__name__}: {exc}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Check a LimiX environment without downloading models or running inference.")
    parser.add_argument("--config", type=Path, help="Optional LimiX inference config JSON to inspect.")
    parser.add_argument("--expect-cuda", action="store_true", help="Fail if torch CUDA is unavailable.")
    parser.add_argument("--json", action="store_true", help="Emit a JSON summary instead of text.")
    args = parser.parse_args()

    modules = [
        "torch",
        "numpy",
        "pandas",
        "sklearn",
        "inference.predictor",
        "inference.preprocess",
        "utils.inference_utils",
        "retrieval_extension.retrieval_search_space.init_search_space",
    ]
    imports = {name: try_import(name) for name in modules}

    torch_info: dict[str, Any] = {"available": False}
    torch_ok, _ = imports.get("torch", (False, ""))
    if torch_ok:
        import torch  # type: ignore

        torch_info = {
            "available": True,
            "version": getattr(torch, "__version__", None),
            "cuda_runtime": getattr(torch.version, "cuda", None),
            "cuda_available": bool(torch.cuda.is_available()),
            "cuda_device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
        }
        if torch.cuda.is_available():
            torch_info["cuda_device0"] = torch.cuda.get_device_name(0)
            torch_info["cuda_capability0"] = list(torch.cuda.get_device_capability(0))
            try:
                torch.empty((1,), device="cuda")
                torch_info["tiny_cuda_tensor"] = "passed"
            except Exception as exc:  # pragma: no cover
                torch_info["tiny_cuda_tensor"] = f"failed: {type(exc).__name__}: {exc}"

    config_summary: dict[str, Any] | None = None
    if args.config:
        config = load_config(args.config)
        retrieval_flags = [bool(item["retrieval_config"].get("use_retrieval", False)) for item in config]
        config_summary = {
            "path": str(args.config),
            "pipelines": len(config),
            "uses_retrieval": any(retrieval_flags),
            "all_retrieval_flags": retrieval_flags,
            "cpu_safe": not any(retrieval_flags),
            "top_level_keys": sorted({key for item in config for key in item}),
        }

    failures: list[str] = []
    for name, (ok, detail) in imports.items():
        if not ok:
            failures.append(f"import {name}: {detail}")
    if args.expect_cuda and not torch_info.get("cuda_available", False):
        failures.append("CUDA was expected but torch.cuda.is_available() is false")
    if args.config and config_summary and config_summary["uses_retrieval"] and not torch_info.get("cuda_available", False):
        failures.append("config uses retrieval but CUDA is unavailable; use no-retrieval config on CPU")

    result = {"imports": imports, "torch": torch_info, "config": config_summary, "failures": failures}
    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print("LimiX environment diagnostic")
        for name, (ok, detail) in imports.items():
            print(f"- import {name}: {'OK' if ok else 'FAIL'} ({detail})")
        print(f"- torch: {torch_info}")
        if config_summary:
            print(f"- config: {config_summary}")
        if failures:
            print("Failures:")
            for failure in failures:
                print(f"  - {failure}")
        else:
            print("No diagnostic failures.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
