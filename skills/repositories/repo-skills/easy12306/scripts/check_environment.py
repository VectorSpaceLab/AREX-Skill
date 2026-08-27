#!/usr/bin/env python3
"""Check whether the active Python environment can run easy12306-style code.

This helper is self-contained and does not import any easy12306 source checkout.
It verifies dependency imports and the legacy Keras ImageDataGenerator import path
that the original image-modeling workflow used.
"""
from __future__ import annotations

import argparse
import importlib
import sys

REQUIRED_IMPORTS = [
    "numpy",
    "cv2",
    "scipy.fftpack",
    "requests",
    "matplotlib",
    "sklearn",
    "keras",
    "tensorflow",
]


def version_for(module_name: str, module) -> str:
    version = getattr(module, "__version__", None)
    if version:
        return str(version)
    root = module_name.split(".")[0]
    try:
        root_mod = importlib.import_module(root)
    except Exception:
        return "unknown"
    return str(getattr(root_mod, "__version__", "unknown"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify easy12306 dependency imports and legacy Keras compatibility.")
    parser.add_argument("--allow-keras3", action="store_true", help="Warn instead of failing if the legacy ImageDataGenerator import path is missing.")
    args = parser.parse_args(argv)

    failures: list[str] = []
    print(f"python: {sys.version.split()[0]}")
    for name in REQUIRED_IMPORTS:
        try:
            module = importlib.import_module(name)
        except Exception as exc:  # noqa: BLE001
            failures.append(f"import {name!r} failed: {exc}")
            continue
        print(f"import {name}: OK version={version_for(name, module)}")

    try:
        from keras.preprocessing.image import ImageDataGenerator  # type: ignore
    except Exception as exc:  # noqa: BLE001
        message = (
            "legacy Keras check failed: cannot import "
            f"keras.preprocessing.image.ImageDataGenerator ({exc}). "
            "Use TensorFlow/Keras 2.15-compatible packages for unmodified easy12306 training scripts, "
            "or use bundled adapters that avoid training-only imports for inference."
        )
        if args.allow_keras3:
            print(f"WARNING: {message}")
        else:
            failures.append(message)
    else:
        print(f"legacy Keras ImageDataGenerator import: OK ({ImageDataGenerator})")

    if failures:
        print("RESULT: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
