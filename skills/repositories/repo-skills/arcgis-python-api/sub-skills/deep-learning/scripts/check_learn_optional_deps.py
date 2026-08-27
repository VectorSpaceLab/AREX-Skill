#!/usr/bin/env python3
"""Report optional dependency availability for arcgis.learn.

This script only probes imports and CUDA metadata. It never trains models,
downloads data, opens credentials, or calls ArcGIS services.
"""
from __future__ import annotations

import argparse
import importlib
import json
from typing import Any, Dict


def probe(module_name: str) -> Dict[str, Any]:
    """Import a module and return a small availability record."""
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # noqa: BLE001 - report import failures without aborting.
        return {
            "ok": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }

    result: Dict[str, Any] = {"ok": True}
    version = getattr(module, "__version__", None)
    if version is not None:
        result["version"] = str(version)
    return result


def probe_cuda() -> Dict[str, Any]:
    """Report CUDA status if torch can be imported."""
    try:
        torch = importlib.import_module("torch")
    except Exception as exc:  # noqa: BLE001 - missing torch is part of the report.
        return {
            "available": False,
            "reason": "torch unavailable",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }

    cuda = getattr(torch, "cuda", None)
    if cuda is None:
        return {"available": False, "reason": "torch.cuda unavailable"}

    info: Dict[str, Any] = {}
    try:
        info["available"] = bool(cuda.is_available())
    except Exception as exc:  # noqa: BLE001
        info["available"] = False
        info["error_type"] = type(exc).__name__
        info["error"] = str(exc)

    try:
        info["device_count"] = int(cuda.device_count())
    except Exception:  # noqa: BLE001
        info["device_count"] = None

    torch_version = getattr(torch, "version", None)
    cuda_version = getattr(torch_version, "cuda", None)
    if cuda_version is not None:
        info["version"] = str(cuda_version)

    return info


def human_line(name: str, record: Dict[str, Any]) -> str:
    if record.get("ok"):
        suffix = f" {record['version']}" if record.get("version") else ""
        return f"{name}: OK{suffix}"
    return f"{name}: MISSING {record.get('error_type', 'Error')}: {record.get('error', '')}"


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Safely report arcgis.learn, torch, torchvision, and CUDA availability "
            "without training, downloads, credentials, or service calls."
        )
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args()

    report: Dict[str, Any] = {
        "arcgis": probe("arcgis"),
        "arcgis.learn": probe("arcgis.learn"),
        "torch": probe("torch"),
        "torchvision": probe("torchvision"),
        "cuda": probe_cuda(),
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0

    for name in ("arcgis", "arcgis.learn", "torch", "torchvision"):
        print(human_line(name, report[name]))

    cuda = report["cuda"]
    if cuda.get("available"):
        details = []
        if cuda.get("device_count") is not None:
            details.append(f"device_count={cuda['device_count']}")
        if cuda.get("version"):
            details.append(f"version={cuda['version']}")
        suffix = f" ({', '.join(details)})" if details else ""
        print(f"CUDA: available{suffix}")
    else:
        details = []
        if cuda.get("reason"):
            details.append(str(cuda["reason"]))
        if cuda.get("error"):
            details.append(f"{cuda.get('error_type', 'Error')}: {cuda['error']}")
        suffix = f" ({'; '.join(details)})" if details else ""
        print(f"CUDA: unavailable{suffix}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
