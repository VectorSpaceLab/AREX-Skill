#!/usr/bin/env python3
"""Check Foolbox's local model-zoo loader without network or external weights.

The check intentionally creates its own temporary ``foolbox_model.py`` and
loads it through ``ModelLoader``. It is safe to run from an arbitrary current
working directory. It requires Foolbox and its normal NumPy dependencies to be
installed, but it never imports the original Foolbox checkout by path.
"""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Sequence


MODULE_NAME = "foolbox_model"

FIXTURE_SOURCE = '''\
import numpy as np
from foolbox.models import NumPyModel


def create(scale=1.0):
    def predict(x):
        values = np.asarray(x).reshape(len(x), -1).sum(axis=1)
        scores = values * float(scale)
        return np.stack((scores, -scores), axis=1)

    return NumPyModel(predict, bounds=(0.0, 1.0))
'''


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create a temporary local Foolbox model-zoo fixture and validate "
            "ModelLoader, create() kwargs, bounds, and a NumPy prediction. "
            "No network or external weights are used."
        )
    )
    parser.add_argument(
        "--keep",
        action="store_true",
        help="keep the temporary fixture and print its absolute path",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    # Parse before importing Foolbox so --help works even in an incomplete
    # environment and never needs to inspect the caller's working directory.
    args = parse_args(argv)

    try:
        import numpy as np
        import foolbox
        from foolbox.zoo import ModelLoader
    except ImportError as exc:
        print(
            "Cannot run the local zoo check: install Foolbox and its NumPy "
            f"runtime dependencies first ({exc}).",
            file=sys.stderr,
        )
        return 2

    fixture = Path(tempfile.mkdtemp(prefix="foolbox-zoo-check-")).resolve()
    module_path = fixture / f"{MODULE_NAME}.py"
    module_path.write_text(FIXTURE_SOURCE, encoding="utf-8")

    # ModelLoader's documented implementation leaves both the path and module
    # in process-global import state. The cleanup below makes this one-shot
    # checker safe when embedded or invoked repeatedly in a test runner.
    old_module = sys.modules.pop(MODULE_NAME, None)
    try:
        model = ModelLoader.get().load(
            str(fixture), module_name=MODULE_NAME, scale=2.0
        )
        if not isinstance(model, foolbox.Model):
            raise AssertionError(
                "create() returned an object that is not a Foolbox Model"
            )
        if tuple(model.bounds) != (0.0, 1.0):
            raise AssertionError(f"unexpected model bounds: {model.bounds!r}")

        inputs = np.asarray([[0.25, 0.50], [0.75, 0.10]], dtype=np.float32)
        predictions = np.asarray(model(inputs))
        expected_values = inputs.reshape(len(inputs), -1).sum(axis=1) * 2.0
        expected = np.stack((expected_values, -expected_values), axis=1)
        if predictions.shape != expected.shape or not np.allclose(
            predictions, expected
        ):
            raise AssertionError(
                f"unexpected prediction: got {predictions!r}, expected {expected!r}"
            )

        print("PASS: local Foolbox zoo loader contract validated")
        print(f"  model type: {type(model).__name__}")
        print(f"  bounds: {tuple(model.bounds)!r}")
        print(f"  fixture: {fixture}")
        return 0
    except Exception as exc:
        print(f"FAIL: local Foolbox zoo loader check: {exc}", file=sys.stderr)
        return 1
    finally:
        while str(fixture) in sys.path:
            sys.path.remove(str(fixture))
        sys.modules.pop(MODULE_NAME, None)
        if old_module is not None:
            sys.modules[MODULE_NAME] = old_module
        if not args.keep:
            shutil.rmtree(fixture, ignore_errors=True)
        else:
            print(f"Kept fixture: {fixture}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
