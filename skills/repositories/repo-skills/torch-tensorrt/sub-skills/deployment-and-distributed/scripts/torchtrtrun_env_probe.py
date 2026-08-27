#!/usr/bin/env python3
"""Probe Torch-TensorRT distributed launcher environment without spawning workers."""

from __future__ import annotations

import argparse
import importlib
import json
import os
import shutil
from typing import Any, Dict


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe torchtrtrun/NCCL-related environment data safely.")
    parser.add_argument("--json", action="store_true", help="print JSON output")
    args = parser.parse_args()

    report: Dict[str, Any] = {"ok": False}
    try:
        import torch  # type: ignore
        import torch_tensorrt  # type: ignore

        dist = importlib.import_module("torch_tensorrt.distributed.run")
        report["torch"] = getattr(torch, "__version__", "unknown")
        report["torch_tensorrt"] = getattr(torch_tensorrt, "__version__", "unknown")
        report["features"] = repr(getattr(torch_tensorrt, "ENABLED_FEATURES", "missing"))
        report["torchtrtrun"] = shutil.which("torchtrtrun")
        report["python_module_entry"] = bool(hasattr(dist, "main"))
        report["cuda_visible_devices"] = os.environ.get("CUDA_VISIBLE_DEVICES")
        report["device_count"] = int(torch.cuda.device_count()) if torch.cuda.is_available() else 0
        report["nccl_available"] = bool(getattr(torch.distributed, "is_nccl_available", lambda: False)())
        report["ok"] = True
    except Exception as exc:  # pragma: no cover
        report["error"] = f"{type(exc).__name__}: {exc}"

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        for key, value in report.items():
            print(f"{key}: {value}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
