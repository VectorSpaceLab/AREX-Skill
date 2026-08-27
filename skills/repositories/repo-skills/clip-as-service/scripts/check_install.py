#!/usr/bin/env python3
"""Safe CLIP-as-service import and optional-backend check.

Examples:
  python scripts/check_install.py
  python scripts/check_install.py --client-only
  python scripts/check_install.py --check-search --check-cuda

The default check imports packages and inspects versions only. It does not start
servers, contact endpoints, or download model weights.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from importlib.metadata import PackageNotFoundError, version

os.environ.setdefault("NO_VERSION_CHECK", "1")


def dist_version(name: str) -> str | None:
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def import_result(module: str) -> dict:
    try:
        mod = importlib.import_module(module)
        return {
            "ok": True,
            "version": getattr(mod, "__version__", None),
        }
    except Exception as exc:  # noqa: BLE001 - diagnostics should not hide import type
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check CLIP-as-service imports and optional backends safely.")
    parser.add_argument("--client-only", action="store_true", help="Require only clip_client.")
    parser.add_argument("--server-only", action="store_true", help="Require only clip_server.")
    parser.add_argument("--check-search", action="store_true", help="Also check AnnLite import for search flows.")
    parser.add_argument("--check-onnx", action="store_true", help="Also check ONNX Runtime executor import.")
    parser.add_argument("--check-tensorrt", action="store_true", help="Also check TensorRT executor import.")
    parser.add_argument("--check-cuda", action="store_true", help="Also run a tiny torch CUDA availability/allocation check.")
    parser.add_argument("--json", action="store_true", help="Emit JSON only.")
    args = parser.parse_args(argv)

    modules: list[str] = []
    if not args.server_only:
        modules.append("clip_client")
    if not args.client_only:
        modules.append("clip_server")
    if args.check_search:
        modules.append("annlite")
    if args.check_onnx:
        modules.append("clip_server.executors.clip_onnx")
    if args.check_tensorrt:
        modules.append("clip_server.executors.clip_tensorrt")

    report = {
        "python": sys.version.split()[0],
        "distributions": {
            "clip-client": dist_version("clip-client"),
            "clip-server": dist_version("clip-server"),
            "annlite": dist_version("annlite"),
        },
        "imports": {module: import_result(module) for module in modules},
        "cuda": None,
    }

    if args.check_cuda:
        try:
            import torch

            cuda = {"available": torch.cuda.is_available(), "device_count": torch.cuda.device_count()}
            if torch.cuda.is_available():
                tensor = torch.tensor([1.0], device="cuda")
                cuda.update({"device0": torch.cuda.get_device_name(0), "tiny_tensor_sum": float(tensor.sum().item())})
            report["cuda"] = cuda
        except Exception as exc:  # noqa: BLE001
            report["cuda"] = {"available": False, "error": f"{type(exc).__name__}: {exc}"}

    failed = [name for name, item in report["imports"].items() if not item.get("ok")]
    if args.check_cuda and report["cuda"] and report["cuda"].get("error"):
        failed.append("cuda")

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
        if failed:
            print("\nFAILED checks:", ", ".join(failed), file=sys.stderr)
            print("Install the missing package or optional extra before using that capability.", file=sys.stderr)

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
