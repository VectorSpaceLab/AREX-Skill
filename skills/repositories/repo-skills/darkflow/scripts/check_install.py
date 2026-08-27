#!/usr/bin/env python3
"""Check a Darkflow install from any working directory.

This helper is safe to run after a package install or editable install.
It imports the legacy TensorFlow stack, prints the verified versions,
and reports the core Darkflow signatures used by the skill tree.

Optional:
  --repo-root PATH   Add a local checkout to sys.path before importing.
"""

import argparse
import inspect
import sys
from pathlib import Path


def _add_repo_root(repo_root):
    if not repo_root:
        return
    path = Path(repo_root).expanduser().resolve()
    sys.path.insert(0, str(path))


def _optional_version(module, attr="__version__"):
    return getattr(module, attr, "unknown")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Verify a Darkflow install and print the core runtime facts."
    )
    parser.add_argument(
        "--repo-root",
        help="Optional local checkout to place at the front of sys.path before imports.",
    )
    args = parser.parse_args(argv)
    _add_repo_root(args.repo_root)

    try:
        import darkflow
        from darkflow import version as darkflow_version
        from darkflow.defaults import argHandler
        from darkflow.net.build import TFNet
        import cv2
        import numpy as np
        import tensorflow as tf
    except Exception as exc:  # pragma: no cover - this is a diagnostic helper.
        print(f"Darkflow install check failed: {exc}", file=sys.stderr)
        return 1

    try:
        import Cython
    except Exception:
        Cython = None

    flags = argHandler()
    flags.setDefaults()

    print("darkflow_version", darkflow_version.__version__)
    print("tensorflow_version", _optional_version(tf))
    print("opencv_version", _optional_version(cv2))
    print("numpy_version", _optional_version(np))
    if Cython is not None:
        print("cython_version", _optional_version(Cython))
    else:
        print("cython_version", "not_installed")
    print("TFNet_signature", inspect.signature(TFNet))
    print("TFNet_return_predict_signature", inspect.signature(TFNet.return_predict))
    print("default_imgdir", flags.imgdir)
    print("default_gpu", flags.gpu)
    print("default_model", flags.model)
    print("default_savepb", flags.savepb)

    built_with_cuda = getattr(getattr(tf, "test", None), "is_built_with_cuda", None)
    if callable(built_with_cuda):
        try:
            print("tensorflow_built_with_cuda", built_with_cuda())
        except Exception as exc:
            print("tensorflow_built_with_cuda", f"error: {exc}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
