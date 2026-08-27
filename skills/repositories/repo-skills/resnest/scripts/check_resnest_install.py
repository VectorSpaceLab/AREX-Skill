#!/usr/bin/env python3
"""Check installed ResNeSt package surfaces without downloads or training.

The default check imports the package, runs a tiny PyTorch no-pretrained forward
when PyTorch is available, and reports optional Gluon/Detectron2 availability.
It is safe to run from any current working directory after installing ResNeSt.
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
from importlib import metadata
from typing import Any, Dict, List

CORE_MODELS = ("resnest50", "resnest101", "resnest200", "resnest269")
FAST_MODELS = (
    "resnest50_fast_1s1x64d",
    "resnest50_fast_2s1x64d",
    "resnest50_fast_4s1x64d",
    "resnest50_fast_1s2x40d",
    "resnest50_fast_2s2x40d",
    "resnest50_fast_4s2x40d",
    "resnest50_fast_1s4x24d",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run safe ResNeSt import/API/backend checks without downloading weights.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--model", default="resnest50", choices=CORE_MODELS + FAST_MODELS,
                        help="PyTorch factory to smoke when --skip-pytorch is not set.")
    parser.add_argument("--image-size", type=int, default=64,
                        help="Square input size for the PyTorch no-pretrained smoke.")
    parser.add_argument("--batch-size", type=int, default=1,
                        help="Batch size for the PyTorch no-pretrained smoke.")
    parser.add_argument("--skip-pytorch", action="store_true",
                        help="Only check package metadata and optional backend imports.")
    parser.add_argument("--check-cuda", action="store_true",
                        help="Also allocate a tiny CUDA tensor when torch reports CUDA availability.")
    parser.add_argument("--strict-optional", action="store_true",
                        help="Return non-zero when optional Gluon or Detectron2 imports are missing.")
    return parser.parse_args()


def import_status(module_name: str) -> Dict[str, Any]:
    try:
        module = importlib.import_module(module_name)
        return {"available": True, "version": getattr(module, "__version__", None)}
    except ModuleNotFoundError as exc:
        return {"available": False, "missing": exc.name, "error_type": exc.__class__.__name__}
    except Exception as exc:  # optional compiled imports can fail after module resolution
        return {"available": False, "error_type": exc.__class__.__name__, "error": str(exc)}


def run_pytorch_smoke(model_name: str, image_size: int, batch_size: int, check_cuda: bool) -> Dict[str, Any]:
    status: Dict[str, Any] = {"requested": True, "model": model_name}
    try:
        import torch
        import resnest.torch as resnest_torch
        from resnest.torch.models.splat import SplAtConv2d
    except ModuleNotFoundError as exc:
        status.update({"ok": False, "missing": exc.name, "error_type": exc.__class__.__name__})
        return status
    except Exception as exc:
        status.update({"ok": False, "error_type": exc.__class__.__name__, "error": str(exc)})
        return status

    factory = getattr(resnest_torch, model_name, None)
    if factory is None:
        status.update({"ok": False, "error": f"factory {model_name!r} was not exported from resnest.torch"})
        return status

    try:
        model = factory(pretrained=False)
        model.eval()
        x = torch.zeros(batch_size, 3, image_size, image_size)
        with torch.no_grad():
            y = model(x)
        splat = SplAtConv2d(4, 4, kernel_size=3, padding=1, radix=2, groups=1, bias=False)
        with torch.no_grad():
            z = splat(torch.zeros(batch_size, 4, 8, 8))
        status.update({
            "ok": True,
            "torch_version": getattr(torch, "__version__", None),
            "output_shape": list(y.shape),
            "splat_output_shape": list(z.shape),
            "cuda_available": bool(torch.cuda.is_available()),
        })
        if check_cuda:
            if torch.cuda.is_available():
                t = torch.ones(1, device="cuda")
                status["cuda_smoke"] = {"ok": True, "value": float(t.item()), "device": torch.cuda.get_device_name(0)}
            else:
                status["cuda_smoke"] = {"ok": False, "reason": "torch.cuda.is_available() is false"}
    except Exception as exc:
        status.update({"ok": False, "error_type": exc.__class__.__name__, "error": str(exc)})
    return status


def main() -> int:
    args = parse_args()
    if args.image_size <= 0 or args.batch_size <= 0:
        print("ERROR: --image-size and --batch-size must be positive integers.", file=sys.stderr)
        return 2

    payload: Dict[str, Any] = {"status": "ok", "checks": {}}
    try:
        payload["distribution_version"] = metadata.version("resnest")
    except metadata.PackageNotFoundError:
        payload["status"] = "failed"
        payload["distribution_version"] = None
        payload["checks"]["metadata"] = {"ok": False, "message": "resnest distribution metadata was not found"}

    payload["checks"]["resnest"] = import_status("resnest")
    payload["checks"]["resnest.torch"] = import_status("resnest.torch")
    payload["checks"]["mxnet"] = import_status("mxnet")
    payload["checks"]["resnest.gluon"] = import_status("resnest.gluon")
    payload["checks"]["detectron2"] = import_status("detectron2")
    payload["checks"]["resnest.d2"] = import_status("resnest.d2")

    if not args.skip_pytorch:
        payload["checks"]["pytorch_smoke"] = run_pytorch_smoke(
            args.model, args.image_size, args.batch_size, args.check_cuda
        )

    required_failed = []
    for key in ["resnest", "resnest.torch"]:
        if not payload["checks"].get(key, {}).get("available"):
            required_failed.append(key)
    if not args.skip_pytorch and not payload["checks"].get("pytorch_smoke", {}).get("ok"):
        required_failed.append("pytorch_smoke")

    optional_failed = []
    if args.strict_optional:
        for key in ["resnest.gluon", "resnest.d2"]:
            if not payload["checks"].get(key, {}).get("available"):
                optional_failed.append(key)

    if required_failed or optional_failed or payload["status"] == "failed":
        payload["status"] = "failed"
        payload["failed_required"] = required_failed
        payload["failed_optional"] = optional_failed
        exit_code = 2
    else:
        exit_code = 0

    print(json.dumps(payload, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
