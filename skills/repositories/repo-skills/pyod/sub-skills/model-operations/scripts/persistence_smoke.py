#!/usr/bin/env python3
"""Safe PyOD persistence smoke check.

The script fits a tiny deterministic detector, saves it to a temporary
joblib file through pyod.utils.persistence.save, verifies that load() refuses
untrusted deserialization, loads the trusted temp artifact, and compares
scores before and after the round-trip. It never reads user-provided pickle
files and writes only inside a TemporaryDirectory unless --keep-temp is set
for debugging.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

import numpy as np


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a safe temporary PyOD persistence round-trip smoke check."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit a machine-readable JSON summary instead of text",
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="keep the temporary directory for debugging and print its path",
    )
    parser.add_argument(
        "--n-train",
        type=int,
        default=80,
        help="number of synthetic training rows (default: 80)",
    )
    parser.add_argument(
        "--n-test",
        type=int,
        default=20,
        help="number of synthetic test rows (default: 20)",
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
        help="random seed for data generation and detector (default: 42)",
    )
    return parser


def _run(args: argparse.Namespace) -> dict[str, object]:
    if args.n_train < 20:
        raise ValueError("--n-train must be at least 20 for a stable smoke check")
    if args.n_test < 1:
        raise ValueError("--n-test must be at least 1")

    from pyod import __version__ as pyod_version
    from pyod.models.iforest import IForest
    from pyod.utils.data import generate_data
    from pyod.utils.persistence import load, save

    X_train, X_test, _, _ = generate_data(
        n_train=args.n_train,
        n_test=args.n_test,
        n_features=4,
        contamination=0.1,
        random_state=args.random_state,
    )

    clf = IForest(
        contamination=0.1,
        n_estimators=25,
        random_state=args.random_state,
    ).fit(X_train)
    expected = clf.decision_function(X_test)

    temp_ctx = tempfile.TemporaryDirectory(prefix="pyod-persistence-smoke-")
    temp_dir = Path(temp_ctx.name)
    try:
        artifact = temp_dir / "iforest.pyod.joblib"
        save(clf, artifact, metadata={"purpose": "persistence_smoke"})

        trust_guard_ok = False
        try:
            load(artifact)
        except ValueError as exc:
            trust_guard_ok = "trusted" in str(exc).lower()
        if not trust_guard_ok:
            raise AssertionError("load() did not enforce the trusted=True guard")

        loaded, envelope = load(artifact, trusted=True, return_metadata=True)
        got = loaded.decision_function(X_test)

        if got.shape != expected.shape:
            raise AssertionError(f"score shape mismatch: {got.shape} != {expected.shape}")
        if not np.isfinite(got).all():
            raise AssertionError("loaded model produced non-finite scores")
        if not np.allclose(got, expected, rtol=1e-12, atol=1e-12):
            max_abs = float(np.max(np.abs(got - expected)))
            raise AssertionError(f"round-trip scores changed; max_abs_diff={max_abs}")

        labels = loaded.predict(X_test)
        unique_labels = sorted(int(x) for x in np.unique(labels))
        if not set(unique_labels).issubset({0, 1}):
            raise AssertionError(f"unexpected labels after load: {unique_labels}")

        result = {
            "status": "ok",
            "pyod_version": pyod_version,
            "model_class": type(loaded).__name__,
            "artifact_was_temp": True,
            "trusted_guard_verified": trust_guard_ok,
            "metadata_purpose": (envelope.get("metadata") or {}).get("purpose"),
            "score_shape": list(got.shape),
            "score_max_abs_diff": float(np.max(np.abs(got - expected))),
            "labels": unique_labels,
            "temp_dir": str(temp_dir) if args.keep_temp else None,
        }
    except Exception:
        if not args.keep_temp:
            temp_ctx.cleanup()
        raise
    else:
        if not args.keep_temp:
            temp_ctx.cleanup()
        return result


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        result = _run(args)
    except Exception as exc:  # pragma: no cover - exercised by CLI failures
        if args.json:
            print(json.dumps({"status": "error", "error": str(exc)}, sort_keys=True))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        print("PyOD persistence smoke: OK")
        print(f"  PyOD version: {result['pyod_version']}")
        print(f"  Model class: {result['model_class']}")
        print(f"  Score shape: {result['score_shape']}")
        print(f"  Max abs diff: {result['score_max_abs_diff']}")
        print("  Trust guard verified: yes")
        if result.get("temp_dir"):
            print(f"  Kept temp dir: {result['temp_dir']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
