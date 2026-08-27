#!/usr/bin/env python3
"""Report torch accelerator visibility and AutoTrain backend keys.

This is a safe inspection helper; it does not launch training or contact hosted services.
"""

from __future__ import annotations

import json
import sys
from typing import Any


def main() -> int:
    payload: dict[str, Any] = {"python": sys.version.split()[0]}

    try:
        import torch  # type: ignore

        payload["torch"] = {
            "version": getattr(torch, "__version__", None),
            "cuda_available": torch.cuda.is_available(),
            "cuda_device_count": torch.cuda.device_count(),
            "cuda_devices": [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())]
            if torch.cuda.is_available()
            else [],
            "mps_available": bool(getattr(getattr(torch, "backends", None), "mps", None) and torch.backends.mps.is_available()),
        }
    except Exception as exc:  # pragma: no cover - environment triage
        payload["torch_error"] = repr(exc)

    try:
        from autotrain.backends.base import AVAILABLE_HARDWARE  # type: ignore

        payload["autotrain_available_hardware"] = {
            "count": len(AVAILABLE_HARDWARE),
            "keys": sorted(AVAILABLE_HARDWARE.keys()),
        }
    except Exception as exc:  # pragma: no cover - environment triage
        payload["autotrain_backend_error"] = repr(exc)

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if "torch_error" not in payload and "autotrain_backend_error" not in payload else 1


if __name__ == "__main__":
    raise SystemExit(main())
