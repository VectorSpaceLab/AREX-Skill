#!/usr/bin/env python3
"""Print a safe StarDist environment diagnostic without revealing install paths."""
from __future__ import annotations

import importlib
import inspect
import sys


def probe(name: str) -> str:
    try:
        module = importlib.import_module(name)
        return "ok" if getattr(module, "__version__", None) is None else f"ok ({module.__version__})"
    except Exception as exc:
        return f"error: {type(exc).__name__}: {exc}"


def main() -> int:
    print(f"python: {sys.version.split()[0]}")
    for name in ("numpy", "tensorflow", "stardist", "stardist.models", "stardist.geometry", "stardist.matching", "stardist.data"):
        print(f"{name}: {probe(name)}")
    try:
        import tensorflow as tf
        print(f"tensorflow_gpu_devices: {len(tf.config.list_physical_devices('GPU'))}")
    except Exception as exc:
        print(f"tensorflow_gpu_devices: unavailable ({type(exc).__name__})")
    try:
        from stardist.models import StarDist2D, StarDist3D
        print(f"StarDist2D.predict_instances: {inspect.signature(StarDist2D.predict_instances)}")
        print(f"StarDist3D.predict_instances: {inspect.signature(StarDist3D.predict_instances)}")
    except Exception as exc:
        print(f"model_signatures: unavailable ({type(exc).__name__}: {exc})")
    for name in ("stardist.lib.stardist2d", "stardist.lib.stardist3d"):
        print(f"{name}: {probe(name)}")
    for name in ("gputools", "bioimageio.core"):
        print(f"optional {name}: {probe(name)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
