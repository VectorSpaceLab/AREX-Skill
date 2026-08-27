#!/usr/bin/env python3
"""Read-only ExecuTorch import-surface diagnostic.

Example:
  python scripts/check_import_surface.py
"""
import argparse
import importlib
import json

MODULES = [
    "executorch.exir",
    "executorch.export",
    "executorch.runtime",
    "executorch.extension.pybindings.portable_lib",
    "executorch.devtools.inspector",
    "executorch.backends.xnnpack.partition.xnnpack_partitioner",
    "executorch.backends.qualcomm.partition.qnn_partitioner",
    "executorch.backends.cortex_m.quantizer.quantizer",
]


def probe(name: str) -> dict:
    try:
        mod = importlib.import_module(name)
        return {"module": name, "ok": True, "file": getattr(mod, "__file__", None)}
    except Exception as exc:
        return {"module": name, "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe ExecuTorch import surfaces without installing packages or running models.")
    parser.add_argument("--module", action="append", help="Specific module to probe; repeat for multiple modules. Default probes the curated ExecuTorch surface.")
    args = parser.parse_args()
    modules = args.module or MODULES
    print(json.dumps([probe(name) for name in modules], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

