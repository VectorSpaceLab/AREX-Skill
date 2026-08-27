#!/usr/bin/env python3
"""Read-only GIMP-ML environment diagnostic; no downloads, servers, or writes."""
from __future__ import annotations

import argparse
import importlib.util
import platform
import shutil
import sys

COMMON = ("numpy", "scipy", "cv2", "PIL", "requests", "fastapi", "uvicorn", "psutil", "torch")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Report common Python imports and host prerequisites without changing the system."
    )
    parser.add_argument("--cuda", action="store_true", help="probe Torch CUDA visibility without allocating tensors")
    parser.add_argument("--require", action="append", choices=COMMON, help="fail if one import is unavailable")
    args = parser.parse_args()

    print(f"python: {sys.version.split()[0]}")
    print(f"platform: {platform.platform()}")
    print(f"gimp executable: {'present' if shutil.which('gimp') else 'missing'}")
    print(f"python2 executable: {'present' if shutil.which('python2') else 'missing'}")
    missing = []
    for name in COMMON:
        ok = importlib.util.find_spec(name) is not None
        print(f"import {name}: {'available' if ok else 'missing'}")
        if not ok:
            missing.append(name)
    if args.cuda:
        try:
            import torch
            available = bool(torch.cuda.is_available())
            print(f"torch cuda visible: {available}")
            if available:
                print(f"torch cuda devices: {torch.cuda.device_count()}")
                print("allocation test: skipped")
        except Exception as exc:
            print(f"torch cuda probe: error {type(exc).__name__}: {exc}")
            return 2
    required = set(args.require or ())
    failed = sorted(required.intersection(missing))
    if failed:
        print("required imports missing: " + ", ".join(failed))
        return 1
    print("diagnostic complete; importability is not proof of GIMP, weights, provider, or model compatibility")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
