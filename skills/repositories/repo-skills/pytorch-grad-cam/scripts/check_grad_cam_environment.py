#!/usr/bin/env python3
"""Safe grad-cam environment diagnostic.

This helper imports the public package, checks selected optional backends, and
runs no model downloads or training. Example:

  python check_grad_cam_environment.py --check-cuda
"""

from __future__ import annotations

import argparse
import importlib
from importlib.metadata import PackageNotFoundError, version


def _try_import(name: str) -> tuple[bool, str]:
    try:
        module = importlib.import_module(name)
        return True, getattr(module, "__version__", "imported")
    except Exception as exc:  # pragma: no cover - diagnostic path
        return False, f"{type(exc).__name__}: {exc}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Check grad-cam imports and optional backends safely.")
    parser.add_argument("--check-cuda", action="store_true", help="Also allocate a tiny CUDA tensor if torch reports CUDA available.")
    parser.add_argument("--check-optional", action="store_true", help="Probe optional timm/transformers imports used by examples.")
    args = parser.parse_args()

    try:
        dist_version = version("grad-cam")
    except PackageNotFoundError:
        print("FAIL: distribution 'grad-cam' is not installed. Try: pip install grad-cam")
        return 1
    print(f"grad-cam distribution: {dist_version}")

    required = [
        "pytorch_grad_cam",
        "pytorch_grad_cam.utils.model_targets",
        "pytorch_grad_cam.utils.reshape_transforms",
        "pytorch_grad_cam.metrics.road",
        "pytorch_grad_cam.feature_factorization.deep_feature_factorization",
    ]
    failed = False
    for name in required:
        ok, detail = _try_import(name)
        print(("OK" if ok else "FAIL"), name, detail)
        failed = failed or not ok

    ok, detail = _try_import("torch")
    if ok:
        import torch
        print(f"torch: {torch.__version__}; cuda={torch.version.cuda}; cuda_available={torch.cuda.is_available()}")
        if args.check_cuda:
            if torch.cuda.is_available():
                x = torch.ones(1, device="cuda")
                print(f"OK cuda tiny tensor on {torch.cuda.get_device_name(0)}: {float(x.sum().cpu())}")
            else:
                print("WARN cuda check requested but torch.cuda.is_available() is False")
    else:
        print("FAIL torch", detail)
        failed = True

    if args.check_optional:
        for name in ["timm", "transformers", "habana_frameworks.torch.core"]:
            ok, detail = _try_import(name)
            print(("OK optional" if ok else "MISSING optional"), name, detail)

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
