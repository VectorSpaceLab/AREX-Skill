#!/usr/bin/env python3
"""Safe SAM3 backend/import check.

The script imports SamGeo3, prints model registry/signatures, and optionally
requires CUDA. It does not instantiate SAM3 models or download checkpoints.
"""

from __future__ import annotations

import argparse
import inspect
import json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-cuda", action="store_true", help="Return non-zero unless CUDA is available and a tiny allocation succeeds.")
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    args = parser.parse_args()

    report: dict = {"imports": {}, "registry": {}, "signatures": {}, "cuda": {}}
    ok = True

    try:
        from samgeo.model_registry import AVAILABLE_MODELS, DEFAULT_MODEL_IDS
        from samgeo.samgeo3 import SamGeo3, SamGeo3Video

        report["imports"]["samgeo.samgeo3"] = True
        report["registry"] = {"default": DEFAULT_MODEL_IDS, "available": AVAILABLE_MODELS}
        for label, obj in {
            "SamGeo3": SamGeo3,
            "SamGeo3.generate_masks": SamGeo3.generate_masks,
            "SamGeo3.generate_masks_tiled": SamGeo3.generate_masks_tiled,
            "SamGeo3.predict_inst": SamGeo3.predict_inst,
            "SamGeo3Video": SamGeo3Video,
            "SamGeo3Video.propagate": SamGeo3Video.propagate,
        }.items():
            report["signatures"][label] = str(inspect.signature(obj))
    except Exception as exc:  # noqa: BLE001
        ok = False
        report["imports"]["samgeo.samgeo3"] = f"{type(exc).__name__}: {exc}"

    try:
        import torch

        report["cuda"] = {
            "torch": getattr(torch, "__version__", None),
            "torch_cuda": getattr(torch.version, "cuda", None),
            "available": bool(torch.cuda.is_available()),
            "device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
        }
        if torch.cuda.is_available():
            report["cuda"]["device_name_0"] = torch.cuda.get_device_name(0)
            report["cuda"]["allocation"] = str(torch.empty((1,), device="cuda").device)
        elif args.require_cuda:
            ok = False
    except Exception as exc:  # noqa: BLE001
        report["cuda"] = {"error": f"{type(exc).__name__}: {exc}"}
        if args.require_cuda:
            ok = False

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for key, value in report.items():
            print(f"{key}: {value}")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
