#!/usr/bin/env python3
"""Deterministic Hummingbird smoke test for tiny fitted sklearn classifiers.

The script imports Hummingbird normally from the active Python environment. It
never modifies sys.path and does not require a source checkout.
"""

from __future__ import annotations

import argparse
import json
import sys
import warnings
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class SmokeResult:
    ok: bool
    backend: str
    model: str
    mode: str
    n_eval_rows: int
    n_features: int
    batch_size: Optional[int]
    remainder_size: int
    prediction_shape: Any
    proba_shape: Optional[Any]
    message: str

    def as_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "backend": self.backend,
            "model": self.model,
            "mode": self.mode,
            "n_eval_rows": self.n_eval_rows,
            "n_features": self.n_features,
            "batch_size": self.batch_size,
            "remainder_size": self.remainder_size,
            "prediction_shape": list(self.prediction_shape),
            "proba_shape": None if self.proba_shape is None else list(self.proba_shape),
            "message": self.message,
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Convert a tiny fitted sklearn classifier with hummingbird.ml and "
            "validate prediction/probability parity."
        )
    )
    parser.add_argument(
        "--backend",
        default="torch",
        help="Hummingbird backend string, e.g. torch, pytorch, torch.jit, torchscript, onnx.",
    )
    parser.add_argument(
        "--model",
        choices=["decision-tree", "random-forest"],
        default="decision-tree",
        help="Tiny sklearn classifier to fit before conversion.",
    )
    parser.add_argument(
        "--tree-implementation",
        choices=["gemm", "tree_trav", "perf_tree_trav"],
        default=None,
        help="Optional Hummingbird tree_implementation extra_config value.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=None,
        help="If set, use convert_batch with this trace batch size instead of convert.",
    )
    parser.add_argument(
        "--remainder-size",
        type=int,
        default=0,
        help="Remainder rows for convert_batch; must be nonnegative and smaller than --batch-size.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a machine-readable JSON result. Errors are also emitted as JSON.",
    )
    return parser


def _load_dependencies():
    try:
        import numpy as np
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.tree import DecisionTreeClassifier
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(
            "Missing core smoke-test dependency. Install numpy and scikit-learn in the active environment. "
            f"Original import error: {exc}"
        ) from exc

    try:
        from hummingbird.ml import constants, convert, convert_batch
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(
            "Could not import hummingbird.ml from the active environment. Install the hummingbird-ml "
            "distribution and its import-time dependencies. "
            f"Original import error: {exc}"
        ) from exc

    return np, DecisionTreeClassifier, RandomForestClassifier, constants, convert, convert_batch


def _make_data(np, n_rows: int, n_features: int = 5):
    rng = np.random.default_rng(12345)
    x = rng.normal(loc=0.0, scale=1.0, size=(n_rows, n_features)).astype(np.float32)
    score = x[:, 0] + 0.5 * x[:, 1] - 0.25 * x[:, 2]
    y = (score > np.median(score)).astype(np.int64)
    return x, y


def _make_model(kind: str, DecisionTreeClassifier, RandomForestClassifier):
    if kind == "decision-tree":
        return DecisionTreeClassifier(max_depth=3, random_state=7)
    if kind == "random-forest":
        return RandomForestClassifier(n_estimators=5, max_depth=4, random_state=7)
    raise ValueError(f"unsupported model kind: {kind}")


def _assert_close_or_equal(np, actual, expected, *, label: str) -> None:
    actual_arr = np.asarray(actual)
    expected_arr = np.asarray(expected)
    if actual_arr.shape != expected_arr.shape:
        raise AssertionError(
            f"{label} shape mismatch: Hummingbird {actual_arr.shape} vs sklearn {expected_arr.shape}"
        )

    if np.issubdtype(actual_arr.dtype, np.number) and np.issubdtype(expected_arr.dtype, np.number):
        np.testing.assert_allclose(actual_arr, expected_arr, rtol=1e-6, atol=1e-6, err_msg=f"{label} mismatch")
    elif not np.array_equal(actual_arr, expected_arr):
        raise AssertionError(f"{label} mismatch for nonnumeric output")


def run_smoke(args: argparse.Namespace) -> SmokeResult:
    if args.batch_size is not None and args.batch_size <= 0:
        raise ValueError("--batch-size must be a positive integer when provided")
    if args.remainder_size < 0:
        raise ValueError("--remainder-size must be nonnegative")
    if args.batch_size is None and args.remainder_size:
        raise ValueError("--remainder-size is only meaningful with --batch-size")
    if args.batch_size is not None and args.remainder_size >= args.batch_size:
        raise ValueError("--remainder-size must be smaller than --batch-size")

    np, DecisionTreeClassifier, RandomForestClassifier, constants, convert, convert_batch = _load_dependencies()

    if args.batch_size is None:
        n_eval_rows = 18
    else:
        n_eval_rows = args.batch_size * 2 + args.remainder_size
    n_rows = max(24, n_eval_rows)
    x_all, y_all = _make_data(np, n_rows)
    x_eval = x_all[:n_eval_rows]

    skl_model = _make_model(args.model, DecisionTreeClassifier, RandomForestClassifier)
    skl_model.fit(x_all, y_all)

    extra_config: Dict[str, Any] = {}
    if args.tree_implementation:
        extra_config[constants.TREE_IMPLEMENTATION] = args.tree_implementation

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if args.batch_size is None:
            # Supplying test_input is harmless for torch and required by tracing-oriented backends.
            test_input = x_eval[: min(8, len(x_eval))]
            hb_model = convert(skl_model, args.backend, test_input=test_input, extra_config=extra_config)
            mode = "convert"
            effective_batch = None
        else:
            test_input = x_eval[: args.batch_size]
            hb_model = convert_batch(
                skl_model,
                args.backend,
                test_input,
                remainder_size=args.remainder_size,
                extra_config=extra_config,
            )
            mode = "convert_batch"
            effective_batch = args.batch_size

        skl_pred = skl_model.predict(x_eval)
        hb_pred = hb_model.predict(x_eval)
        _assert_close_or_equal(np, hb_pred, skl_pred, label="predict")

        proba_shape = None
        if hasattr(skl_model, "predict_proba") and hasattr(hb_model, "predict_proba"):
            skl_proba = skl_model.predict_proba(x_eval)
            hb_proba = hb_model.predict_proba(x_eval)
            _assert_close_or_equal(np, hb_proba, skl_proba, label="predict_proba")
            proba_shape = np.asarray(hb_proba).shape

    return SmokeResult(
        ok=True,
        backend=args.backend,
        model=args.model,
        mode=mode,
        n_eval_rows=int(n_eval_rows),
        n_features=int(x_eval.shape[1]),
        batch_size=effective_batch,
        remainder_size=int(args.remainder_size),
        prediction_shape=np.asarray(hb_pred).shape,
        proba_shape=proba_shape,
        message="conversion parity smoke passed",
    )


def _error_payload(args: argparse.Namespace, exc: BaseException) -> Dict[str, Any]:
    exc_name = exc.__class__.__name__
    message = str(exc)
    if exc_name in {"MissingBackend"}:
        hint = "Backend is unsupported or its dependency is not installed; inspect hummingbird.ml.backends."
        code = "missing_backend"
    elif exc_name in {"MissingConverter"}:
        hint = "The estimator or one pipeline step has no registered Hummingbird converter."
        code = "missing_converter"
    elif exc_name in {"ImportError", "ModuleNotFoundError"} or "Original import error" in message:
        hint = "Install hummingbird-ml, numpy, scikit-learn, and selected backend/import-time dependencies in this environment."
        code = "import_error"
    elif exc_name == "NotFittedError":
        hint = "Fit the sklearn estimator before conversion."
        code = "not_fitted"
    else:
        hint = "Check backend, test_input shape/dtype, model support, and convert_batch row constraints."
        code = "runtime_error"
    return {
        "ok": False,
        "backend": getattr(args, "backend", None),
        "model": getattr(args, "model", None),
        "error_type": exc_name,
        "error_code": code,
        "message": message,
        "hint": hint,
    }


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        result = run_smoke(args)
    except Exception as exc:  # intentionally concise for smoke CLI use
        payload = _error_payload(args, exc)
        if args.json:
            print(json.dumps(payload, sort_keys=True))
        else:
            print(f"ERROR [{payload['error_code']}]: {payload['message']}", file=sys.stderr)
            print(f"Hint: {payload['hint']}", file=sys.stderr)
        if payload["error_code"] == "missing_backend":
            return 3
        if payload["error_code"] == "missing_converter":
            return 4
        if payload["error_code"] == "import_error":
            return 2
        return 1

    if args.json:
        print(json.dumps(result.as_dict(), sort_keys=True))
    else:
        print(
            f"OK: {result.message}; backend={result.backend}; model={result.model}; "
            f"mode={result.mode}; rows={result.n_eval_rows}; prediction_shape={tuple(result.prediction_shape)}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
