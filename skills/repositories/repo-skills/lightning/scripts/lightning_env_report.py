#!/usr/bin/env python
"""Report safe Lightning import/version/backend facts as JSON or text."""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import platform
import sys
from typing import Any


def _dist_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def _import_status(name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(name)
        return {"ok": True, "version": getattr(module, "__version__", None)}
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def collect() -> dict[str, Any]:
    report: dict[str, Any] = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "distributions": {
            name: _dist_version(name)
            for name in [
                "lightning",
                "pytorch-lightning",
                "lightning-fabric",
                "torch",
                "torchmetrics",
                "lightning-utilities",
                "jsonargparse",
                "requests",
            ]
        },
        "imports": {
            name: _import_status(name)
            for name in ["lightning", "lightning.pytorch", "pytorch_lightning", "lightning.fabric"]
        },
    }
    try:
        import torch

        report["torch_backend"] = {
            "version": torch.__version__,
            "cuda_available": bool(torch.cuda.is_available()),
            "cuda_device_count": int(torch.cuda.device_count()),
            "mps_available": bool(getattr(torch.backends, "mps", None) and torch.backends.mps.is_available()),
        }
    except Exception as exc:
        report["torch_backend"] = {"error": f"{type(exc).__name__}: {exc}"}
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Print safe Lightning environment diagnostics.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    args = parser.parse_args()
    report = collect()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return
    print(f"Python: {report['python']}")
    print(f"Platform: {report['platform']}")
    for name, version in report["distributions"].items():
        print(f"{name}: {version or 'not installed'}")
    for name, status in report["imports"].items():
        print(f"import {name}: {'ok' if status['ok'] else status['error']}")
    print(f"Torch backend: {report['torch_backend']}")


if __name__ == "__main__":
    main()
