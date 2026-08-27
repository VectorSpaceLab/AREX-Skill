#!/usr/bin/env python3
"""Safely report Composer/Torch device availability without launching training."""

from __future__ import annotations

import json
import os
import platform
import sys
import warnings
from typing import Any


def _error_text(exc: BaseException) -> str:
    return f"{type(exc).__name__}: {exc}"


def _cuda_devices(torch_module: Any) -> list[dict[str, Any]]:
    devices: list[dict[str, Any]] = []
    try:
        count = int(torch_module.cuda.device_count())
    except Exception:
        return devices

    for index in range(count):
        item: dict[str, Any] = {"index": index}
        try:
            item["name"] = torch_module.cuda.get_device_name(index)
        except Exception as exc:
            item["name_error"] = _error_text(exc)
        try:
            major, minor = torch_module.cuda.get_device_capability(index)
            item["capability"] = f"{major}.{minor}"
        except Exception as exc:
            item["capability_error"] = _error_text(exc)
        devices.append(item)
    return devices


def main() -> int:
    report: dict[str, Any] = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "rank_env": {
            key: os.environ.get(key)
            for key in [
                "RANK",
                "WORLD_SIZE",
                "LOCAL_RANK",
                "LOCAL_WORLD_SIZE",
                "NODE_RANK",
                "MASTER_ADDR",
                "MASTER_PORT",
                "CUDA_VISIBLE_DEVICES",
            ]
            if os.environ.get(key) is not None
        },
        "training_launch_attempted": False,
    }

    warnings.filterwarnings(
        "ignore",
        message="The pynvml package is deprecated.*",
        category=FutureWarning,
    )

    try:
        import torch
    except Exception as exc:  # pragma: no cover - environment diagnostic path
        report["torch_import_ok"] = False
        report["torch_import_error"] = _error_text(exc)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 2

    report["torch_import_ok"] = True
    report["torch_version"] = getattr(torch, "__version__", None)
    try:
        report["torch_distributed_available"] = bool(torch.distributed.is_available())
    except Exception as exc:
        report["torch_distributed_available_error"] = _error_text(exc)

    try:
        report["cuda_available"] = bool(torch.cuda.is_available())
    except Exception as exc:
        report["cuda_available_error"] = _error_text(exc)
        report["cuda_available"] = False

    try:
        report["cuda_device_count"] = int(torch.cuda.device_count())
    except Exception as exc:
        report["cuda_device_count_error"] = _error_text(exc)
        report["cuda_device_count"] = 0

    if report.get("cuda_available"):
        report["cuda_devices"] = _cuda_devices(torch)
        try:
            report["cuda_current_device"] = int(torch.cuda.current_device())
        except Exception as exc:
            report["cuda_current_device_error"] = _error_text(exc)
    else:
        report["cuda_note"] = (
            "CPU-only probing succeeded. Do not request DeviceGPU or GPU-only "
            "FSDP/TP behavior unless CUDA is made visible."
        )

    try:
        import composer
    except Exception as exc:  # pragma: no cover - environment diagnostic path
        report["composer_import_ok"] = False
        report["composer_import_error"] = _error_text(exc)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0

    report["composer_import_ok"] = True
    report["composer_version"] = getattr(composer, "__version__", None)

    try:
        from composer.utils.device import get_device

        selected = get_device()
        report["composer_get_device_default"] = selected.__class__.__name__
        report["composer_get_device_name"] = getattr(selected, "name", None)
        report["composer_get_device_dist_backend"] = getattr(selected, "dist_backend", None)
    except Exception as exc:
        report["composer_get_device_error"] = _error_text(exc)

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
