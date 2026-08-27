#!/usr/bin/env python3
"""Read-only probe for dependencies and optional Blender availability."""
from __future__ import annotations

import argparse
import importlib
import shutil


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    modules = ["numpy", "scipy", "yaml", "tqdm", "torch", "tensorboardX"]
    result = {}
    for name in modules:
        try:
            module = importlib.import_module(name)
            result[name] = {"available": True, "version": getattr(module, "__version__", "unknown")}
            if name == "torch":
                result[name]["cuda_available"] = bool(module.cuda.is_available())
                result[name]["cuda_devices"] = int(module.cuda.device_count())
        except Exception as exc:  # diagnostics should report optional failures, not hide them
            result[name] = {"available": False, "error": f"{type(exc).__name__}: {exc}"}
    result["blender"] = {"available": shutil.which("blender") is not None, "executable": shutil.which("blender")}
    if args.json:
        import json
        print(json.dumps(result, indent=2))
    else:
        for name, info in result.items():
            print(name, info)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
