#!/usr/bin/env python3
"""Read-only PointCNN compatibility probe.

The probe is intentionally generic: it reports import/API facts and never
creates checkpoints, downloads data, compiles CUDA, or runs a benchmark.
"""
from __future__ import print_function

import argparse
import importlib
import sys


def main():
    parser = argparse.ArgumentParser(description="Probe legacy PointCNN dependencies and TensorFlow APIs.")
    parser.add_argument("--graph-smoke", action="store_true", help="Build a tiny TF1 graph without executing GPU kernels.")
    args = parser.parse_args()

    print("python:", sys.version.replace("\n", " "))
    modules = ("numpy", "scipy", "h5py", "matplotlib", "plyfile", "transforms3d", "tensorflow")
    loaded = {}
    for name in modules:
        try:
            module = importlib.import_module(name)
            loaded[name] = module
            print("{}: import=ok version={}".format(name, getattr(module, "__version__", "unknown")))
        except Exception as exc:
            print("{}: import=error {}".format(name, exc))

    tf = loaded.get("tensorflow")
    if tf is None:
        return 2
    required = ("contrib", "layers", "placeholder", "Session", "py_func")
    missing = [name for name in required if not hasattr(tf, name)]
    print("tensorflow_built_with_cuda:", bool(tf.test.is_built_with_cuda()))
    print("tensorflow_legacy_api_missing:", ",".join(missing) if missing else "none")
    if args.graph_smoke:
        try:
            graph = tf.Graph()
            with graph.as_default():
                x = tf.placeholder(tf.float32, shape=(None, 3), name="probe_x")
                y = tf.reduce_sum(x, axis=1, name="probe_sum")
            print("graph_smoke: ok output={}".format(y.shape))
        except Exception as exc:
            print("graph_smoke: error {}".format(exc))
            return 3
    return 0 if not missing else 4


if __name__ == "__main__":
    sys.exit(main())
