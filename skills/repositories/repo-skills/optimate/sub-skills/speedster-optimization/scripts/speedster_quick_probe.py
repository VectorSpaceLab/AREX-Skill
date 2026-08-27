#!/usr/bin/env python3
"""Safe import/signature/backend probe for Speedster.

Example:
  python scripts/speedster_quick_probe.py --check-cuda
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
from importlib import metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-cuda", action="store_true", help="Probe torch CUDA visibility")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args()

    report = {"speedster": {}, "nebullvm": {}, "cuda": None}
    for module_name, dist_name in [("speedster", "speedster"), ("nebullvm", "nebullvm")]:
        try:
            module = importlib.import_module(module_name)
            report[module_name] = {
                "status": "ok",
                "file": getattr(module, "__file__", None),
                "version": metadata.version(dist_name),
            }
            if module_name == "speedster":
                from speedster import optimize_model, save_model, load_model

                report[module_name]["signatures"] = {
                    "optimize_model": str(inspect.signature(optimize_model)),
                    "save_model": str(inspect.signature(save_model)),
                    "load_model": str(inspect.signature(load_model)),
                }
        except Exception as exc:
            report[module_name] = {"status": "missing", "error": f"{type(exc).__name__}: {exc}"}

    if args.check_cuda:
        try:
            import torch

            report["cuda"] = {
                "status": "ok" if torch.cuda.is_available() else "unavailable",
                "torch": torch.__version__,
                "device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
            }
        except Exception as exc:
            report["cuda"] = {"status": "missing", "error": f"{type(exc).__name__}: {exc}"}

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
