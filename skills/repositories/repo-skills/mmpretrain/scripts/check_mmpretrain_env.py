#!/usr/bin/env python3
"""Check an installed MMPreTrain environment without downloading checkpoints.

Examples:
  python check_mmpretrain_env.py
  python check_mmpretrain_env.py --model resnet18_8xb32_in1k --backend cpu
  python check_mmpretrain_env.py --pattern "swin" --skip-build

The check imports MMPreTrain, verifies OpenMMLab dependency versions, optionally
queries the model zoo, and builds one model with `pretrained=False`. It does not
train, evaluate, download checkpoints, or require the original repository.
"""

from __future__ import annotations

import argparse
import json
import sys
from importlib import metadata
from typing import Any


def _version(dist: str) -> str | None:
    try:
        return metadata.version(dist)
    except metadata.PackageNotFoundError:
        return None


def _check_backend(name: str) -> dict[str, Any]:
    if name == "cpu":
        try:
            import torch
            torch.empty((1,), device="cpu")
            return {"backend": "cpu", "available": True, "torch": torch.__version__}
        except Exception as exc:
            return {"backend": "cpu", "available": False, "error": str(exc)}
    if name == "cuda":
        try:
            import torch
            available = bool(torch.cuda.is_available())
            info = {
                "backend": "cuda",
                "available": available,
                "torch": torch.__version__,
                "torch_cuda": torch.version.cuda,
                "device_count": torch.cuda.device_count(),
            }
            if available:
                info["device0"] = torch.cuda.get_device_name(0)
                info["capability0"] = torch.cuda.get_device_capability(0)
                torch.empty((1,), device="cuda")
            return info
        except Exception as exc:
            return {"backend": "cuda", "available": False, "error": str(exc)}
    return {"backend": name, "available": None, "error": "unsupported backend check; use cpu or cuda"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check installed MMPreTrain package readiness safely.")
    parser.add_argument("--pattern", default="resnet18", help="Model name pattern for list_models")
    parser.add_argument("--model", default="resnet18_8xb32_in1k", help="Model to build with pretrained=False")
    parser.add_argument("--backend", choices=["cpu", "cuda"], default="cpu", help="Backend smoke to run")
    parser.add_argument("--skip-build", action="store_true", help="Do not instantiate the selected model")
    parser.add_argument("--json", action="store_true", help="Print JSON only")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result: dict[str, Any] = {
        "distributions": {name: _version(name) for name in ["mmpretrain", "mmcv", "mmengine", "torch", "torchvision"]},
        "imports": {},
        "backend": None,
        "model_zoo": None,
        "model_build": None,
        "warnings": [],
    }

    try:
        import mmpretrain
        from mmpretrain import get_model, list_models
        result["imports"]["mmpretrain"] = getattr(mmpretrain, "__version__", "imported")
    except Exception as exc:
        result["imports"]["mmpretrain"] = f"FAILED: {exc}"
        if ".mim" in str(exc) or "model-index" in str(exc):
            result["warnings"].append("ModelHub metadata is missing; reinstall with MIM/source package data so .mim/model-index.yml is available.")
        print(json.dumps(result, indent=2, sort_keys=True) if args.json else result, file=sys.stderr)
        return 1

    result["backend"] = _check_backend(args.backend)

    try:
        models = list_models(args.pattern)
        result["model_zoo"] = {"pattern": args.pattern, "count": len(models), "sample": models[:10]}
    except Exception as exc:
        result["model_zoo"] = {"error": str(exc)}
        if ".mim" in str(exc) or "model-index" in str(exc):
            result["warnings"].append("ModelHub metadata is missing; reinstall with MIM/source package data so .mim/model-index.yml is available.")

    if not args.skip_build:
        try:
            model = get_model(args.model, pretrained=False, device="cpu")
            result["model_build"] = {
                "model": args.model,
                "class": type(model).__name__,
                "backbone": type(getattr(model, "backbone", None)).__name__,
                "pretrained": False,
            }
        except Exception as exc:
            result["model_build"] = {"model": args.model, "error": str(exc)}

    ok = (
        str(result["imports"].get("mmpretrain", "")).startswith("FAILED") is False
        and result["backend"] is not None
        and result["backend"].get("available") is not False
        and result["model_zoo"] is not None
        and "error" not in result["model_zoo"]
        and (args.skip_build or "error" not in (result["model_build"] or {}))
    )

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("MMPreTrain environment check")
        print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
