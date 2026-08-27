#!/usr/bin/env python3
"""Read-only DreamerV2 installation and backend diagnostic.

Run with the same Python that will run DreamerV2. It imports core modules,
prints the public API signature and defaults, checks pip metadata, and reports
TensorFlow devices. It never creates a logdir, environment, checkpoint, or
network connection.
"""
import inspect
import importlib.metadata
import sys


def main():
  print("python:", sys.version.split()[0])
  try:
    print("distribution:", importlib.metadata.version("dreamerv2"))
  except importlib.metadata.PackageNotFoundError:
    print("distribution: missing")
  try:
    import tensorflow as tf
    print("tensorflow:", tf.__version__)
    print("gpus:", [d.name for d in tf.config.list_physical_devices("GPU")])
  except Exception as exc:
    print("tensorflow: ERROR {}: {}".format(type(exc).__name__, exc))
    return 2
  try:
    import dreamerv2.api as api
    from dreamerv2 import common
    print("api.train:", inspect.signature(api.train))
    print("default_task:", api.defaults.task)
    print("common.Config:", common.Config)
    print("common.Replay:", inspect.signature(common.Replay))
    print("common.Dummy:", common.Dummy().obs_space["image"])
  except Exception as exc:
    print("dreamerv2: ERROR {}: {}".format(type(exc).__name__, exc))
    return 1
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
