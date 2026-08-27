#!/usr/bin/env python3
"""Report generic TensorRT demo prerequisites without importing repo code.

This helper is intentionally diagnostic: it checks importability and optional
CUDA visibility, but does not build engines, load plugins, open cameras, or
modify files. Use `--cuda` only on an approved GPU host.
"""
from __future__ import annotations
import argparse
import importlib
import sys

MODULES = ("numpy", "cv2", "onnx", "onnxruntime", "tensorrt", "pycuda")

def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cuda", action="store_true", help="probe PyCUDA device count; may initialize a CUDA driver")
    args = p.parse_args(argv)
    print("python:", sys.version.split()[0])
    failures = 0
    for name in MODULES:
        try:
            mod = importlib.import_module(name)
            version = getattr(mod, "__version__", getattr(mod, "VERSION", "unknown"))
            print(f"OK {name}: {version}")
        except Exception as exc:
            failures += 1
            print(f"WARN {name}: {type(exc).__name__}: {exc}")
    if args.cuda:
        try:
            import pycuda.driver as cuda
            cuda.init()
            print(f"CUDA devices: {cuda.Device.count()}")
        except Exception as exc:
            failures += 1
            print(f"WARN CUDA probe: {type(exc).__name__}: {exc}")
    return 1 if failures else 0

if __name__ == "__main__":
    raise SystemExit(main())
