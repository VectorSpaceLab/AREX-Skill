#!/usr/bin/env python3
"""Safe WeNet package and local-model preflight checker.

This helper validates imports, optional backend availability, and local model
folder shape. It never downloads a model and never transcribes audio.

Examples:
  python check_wenet_package.py
  python check_wenet_package.py --device cuda
  python check_wenet_package.py --model-dir /path/to/model_dir --device cpu
"""

from __future__ import annotations

import argparse
import importlib.util
import inspect
import json
import sys
from importlib import metadata
from pathlib import Path
from typing import Any


def _status(ok: bool, **extra: Any) -> dict[str, Any]:
    data = {"ok": ok}
    data.update(extra)
    return data


def check_imports() -> dict[str, Any]:
    try:
        import wenet  # noqa: F401
        from wenet import load_feature, load_model, load_tokenizer
    except Exception as exc:  # pragma: no cover - depends on user env
        return _status(False, error=type(exc).__name__, message=str(exc))

    try:
        version = metadata.version("wenet")
    except metadata.PackageNotFoundError:
        version = None

    return _status(
        True,
        distribution_version=version,
        signatures={
            "load_model": str(inspect.signature(load_model)),
            "load_feature": str(inspect.signature(load_feature)),
            "load_tokenizer": str(inspect.signature(load_tokenizer)),
        },
    )


def check_model_dir(path: Path) -> dict[str, Any]:
    required = ["train.yaml", "final.pt", "units.txt"]
    optional = ["global_cmvn"]
    missing = [name for name in required if not (path / name).is_file()]
    present_optional = [name for name in optional if (path / name).exists()]
    return _status(
        not missing,
        path=str(path),
        missing_required=missing,
        present_optional=present_optional,
        expected_required=required,
        expected_optional=optional,
    )


def check_device(device: str) -> dict[str, Any]:
    if device == "cpu":
        return _status(True, device="cpu", message="CPU requires no accelerator runtime.")

    try:
        import torch
    except Exception as exc:  # pragma: no cover - depends on user env
        return _status(False, device=device, error=type(exc).__name__, message=str(exc))

    if device == "cuda":
        available = bool(torch.cuda.is_available())
        info: dict[str, Any] = {
            "device": "cuda",
            "available": available,
            "torch_version": getattr(torch, "__version__", None),
            "torch_cuda_runtime": getattr(torch.version, "cuda", None),
            "device_count": torch.cuda.device_count() if available else 0,
        }
        if available:
            info["device0"] = torch.cuda.get_device_name(0)
            info["capability0"] = torch.cuda.get_device_capability(0)
        return _status(available, **info)

    if device == "npu":
        spec = importlib.util.find_spec("torch_npu")
        return _status(
            spec is not None,
            device="npu",
            torch_npu_importable=spec is not None,
            message=(
                "torch_npu is importable. Verify CANN/toolkit separately."
                if spec is not None
                else "torch_npu is not importable; install the matching Ascend NPU stack."
            ),
        )

    return _status(False, device=device, message="Unsupported device string.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check WeNet package imports, model directory shape, and backend availability.")
    parser.add_argument("--model-dir", type=Path, help="Local WeNet model directory to validate without loading the model.")
    parser.add_argument("--device", choices=["cpu", "cuda", "npu"], default="cpu", help="Backend availability to check.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    args = parser.parse_args()

    result: dict[str, Any] = {
        "import_check": check_imports(),
        "device_check": check_device(args.device),
    }
    if args.model_dir is not None:
        result["model_dir_check"] = check_model_dir(args.model_dir)

    ok = result["import_check"]["ok"] and result["device_check"]["ok"]
    if "model_dir_check" in result:
        ok = ok and result["model_dir_check"]["ok"]
    result["ok"] = ok

    print(json.dumps(result, indent=2 if args.pretty else None, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
