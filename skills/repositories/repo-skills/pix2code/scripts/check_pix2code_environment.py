#!/usr/bin/env python3
"""Check a Python environment for pix2code workflow dependencies.

This helper is intentionally read-only. It reports available versions and warns
about the historical dependency stack used by pix2code. Example:

    python check_pix2code_environment.py --include-ml
"""

import argparse
import importlib
import sys
from typing import Iterable, Tuple

EXPECTED = {
    "numpy": "1.13.3",
    "h5py": "2.7.1",
    "cv2": "3.3.0.10 or nearby old OpenCV 3.x",
    "keras": "2.1.2",
    "tensorflow": "1.4.0",
}


def module_version(module) -> str:
    for attr in ("__version__", "version"):
        value = getattr(module, attr, None)
        if isinstance(value, str):
            return value
    return "unknown"


def check_modules(modules: Iterable[str]) -> Tuple[int, list]:
    failures = []
    for name in modules:
        try:
            module = importlib.import_module(name)
            print(f"PASS import {name}: {module_version(module)} (expected {EXPECTED.get(name, 'not pinned')})")
        except Exception as exc:  # pragma: no cover - diagnostic path
            failures.append((name, exc))
            print(f"FAIL import {name}: {exc.__class__.__name__}: {exc}")
    return (1 if failures else 0), failures


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Check pix2code dependency imports and legacy-stack compatibility.")
    parser.add_argument("--include-ml", action="store_true", help="also import Keras and TensorFlow 1.x dependencies")
    args = parser.parse_args(argv)

    print(f"Python: {sys.version.split()[0]}")
    modules = ["numpy", "h5py", "cv2"]
    if args.include_ml:
        modules.extend(["keras", "tensorflow"])
    code, failures = check_modules(modules)

    if sys.version_info[:2] > (3, 6):
        print("WARN pix2code's historical TensorFlow/Keras pins usually require a legacy Python environment.")
    if failures:
        print("One or more imports failed. Install the missing legacy dependency or narrow the workflow to DSL-only tasks.")
    else:
        print("Environment import checks completed. This does not prove paper-scale training or model accuracy.")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
