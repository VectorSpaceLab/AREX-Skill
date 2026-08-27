#!/usr/bin/env python3
"""Import-only requirement check for ssd.pytorch notebook/webcam demos."""

from __future__ import annotations

import argparse
import importlib
import json
from typing import Any


def module_status(name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(name)
        return {"module": name, "available": True, "version": getattr(module, "__version__", "unknown")}
    except Exception as exc:  # noqa: BLE001 - diagnostic helper
        return {"module": name, "available": False, "error_type": type(exc).__name__, "error": str(exc)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Check optional demo dependencies without opening webcam or GUI")
    parser.add_argument("--check-jupyter", action="store_true", help="also check notebook-related modules")
    parser.add_argument("--require-imutils", action="store_true", help="return non-zero if imutils is missing")
    parser.add_argument("--require-cuda", action="store_true", help="return non-zero if torch CUDA is unavailable")
    args = parser.parse_args()

    modules = ["torch", "cv2", "imutils"]
    if args.check_jupyter:
        modules.extend(["IPython", "notebook"])
    statuses = [module_status(name) for name in modules]

    cuda: dict[str, Any] = {"available": None}
    torch_status = next((s for s in statuses if s["module"] == "torch" and s["available"]), None)
    if torch_status:
        torch = importlib.import_module("torch")
        cuda = {"available": bool(torch.cuda.is_available()), "device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0}

    report = {
        "ok": True,
        "modules": statuses,
        "cuda": cuda,
        "notes": [
            "No webcam was opened and no GUI window was created.",
            "Actual live demo also needs a camera, display/GUI-capable OpenCV build, and compatible SSD300 weights.",
        ],
    }

    failures = []
    if args.require_imutils and not any(s["module"] == "imutils" and s["available"] for s in statuses):
        failures.append("imutils is required but unavailable")
    if args.require_cuda and not cuda.get("available"):
        failures.append("CUDA is required but torch.cuda.is_available() is false")
    if failures:
        report["ok"] = False
        report["failures"] = failures

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
