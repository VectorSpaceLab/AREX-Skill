#!/usr/bin/env python3
"""Print a compact readiness report for the installed LightX2V package.

This script is intentionally light-weight: it checks the core package import,
then probes a small set of common optional dependencies without triggering any
model loading or generation work.
"""

from __future__ import annotations

import importlib
import json
from typing import Any

CORE_MODULES = ["lightx2v", "torch"]
OPTIONAL_MODULES = [
    "numpy",
    "fastapi",
    "uvicorn",
    "requests",
    "httpx",
    "pydantic",
    "safetensors",
    "imageio",
    "imageio_ffmpeg",
    "torchvision",
    "decord",
    "av",
    "redis",
    "qtorch",
]


def probe_module(name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # pragma: no cover - diagnostic helper
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    report: dict[str, Any] = {"ok": True}
    version = getattr(module, "__version__", None)
    if version is not None:
        report["version"] = str(version)
    return report


def probe_torch() -> dict[str, Any]:
    result = probe_module("torch")
    if not result.get("ok"):
        return result

    import torch

    result["cuda_available"] = bool(torch.cuda.is_available())
    result["cuda_version"] = getattr(torch.version, "cuda", None)
    if torch.cuda.is_available():
        result["device_count"] = int(torch.cuda.device_count())
        try:
            result["device_name"] = torch.cuda.get_device_name(0)
        except Exception as exc:  # pragma: no cover - diagnostic helper
            result["device_name_error"] = f"{type(exc).__name__}: {exc}"
    return result


def probe_lightx2v() -> dict[str, Any]:
    result = probe_module("lightx2v")
    if not result.get("ok"):
        return result

    import lightx2v

    result["package_version"] = getattr(lightx2v, "__version__", None)
    result["pipeline_available"] = hasattr(lightx2v, "LightX2VPipeline")
    return result


def main() -> int:
    report = {
        "core": {
            "lightx2v": probe_lightx2v(),
            "torch": probe_torch(),
        },
        "optional": {name: probe_module(name) for name in OPTIONAL_MODULES},
    }

    core_ok = bool(report["core"]["lightx2v"].get("ok")) and bool(report["core"]["torch"].get("ok"))
    report["ready"] = core_ok

    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, default=str))
    return 0 if core_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
