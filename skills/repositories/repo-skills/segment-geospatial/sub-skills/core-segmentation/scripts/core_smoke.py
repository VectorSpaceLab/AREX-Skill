#!/usr/bin/env python3
"""Safe import/signature smoke for SamGeo SAM1 and SAM2.

This script does not construct models or download checkpoints. It only imports
public classes, prints selected signatures, and reports torch device visibility.
"""

from __future__ import annotations

import argparse
import inspect
import json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    args = parser.parse_args()

    report = {"imports": {}, "signatures": {}, "device": {}}
    try:
        from samgeo.samgeo import SamGeo
        from samgeo.samgeo2 import SamGeo2

        report["imports"]["SamGeo"] = True
        report["imports"]["SamGeo2"] = True
        for label, obj in {
            "SamGeo": SamGeo,
            "SamGeo.generate": SamGeo.generate,
            "SamGeo.predict": SamGeo.predict,
            "SamGeo2": SamGeo2,
            "SamGeo2.generate": SamGeo2.generate,
            "SamGeo2.predict": SamGeo2.predict,
            "SamGeo2.predict_video": SamGeo2.predict_video,
        }.items():
            report["signatures"][label] = str(inspect.signature(obj))
    except Exception as exc:  # noqa: BLE001
        report["error"] = f"{type(exc).__name__}: {exc}"

    try:
        import torch

        report["device"] = {
            "torch": getattr(torch, "__version__", None),
            "cuda": bool(torch.cuda.is_available()),
            "device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
        }
    except Exception as exc:  # noqa: BLE001
        report["device"] = {"error": f"{type(exc).__name__}: {exc}"}

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for key, value in report.items():
            print(f"{key}: {value}")

    return 0 if "error" not in report else 1


if __name__ == "__main__":
    raise SystemExit(main())
