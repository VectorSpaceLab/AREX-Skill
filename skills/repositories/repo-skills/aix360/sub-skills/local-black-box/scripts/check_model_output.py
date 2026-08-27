#!/usr/bin/env python3
"""Validate small model-output contracts used by local explainers.

This helper is intentionally dependency-light. It can validate JSON-captured
outputs or run built-in tiny fixtures; it never imports a model, downloads
anything, or writes files.
"""
from __future__ import annotations

import argparse
import json
from typing import Any, Optional, Tuple

import numpy as np


KINDS = ("probabilities", "scalar", "scores", "labels")


def validate_model_output(
    output: Any,
    n_rows: int,
    *,
    kind: str,
    n_classes: Optional[int] = None,
) -> Tuple[int, ...]:
    """Validate and return the shape of an explainer model output.

    ``probabilities`` requires a finite 2-D matrix with one row per input,
    values in [0, 1], and rows summing to one. ``scalar`` accepts a scalar for
    one row or a vector/one-column matrix for a batch. ``scores`` accepts a
    finite vector or finite 2-D batch output. ``labels`` accepts a vector or
    one-column integer-like output.
    """
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {KINDS}, got {kind!r}")
    if not isinstance(n_rows, int) or n_rows < 1:
        raise ValueError("n_rows must be a positive integer")
    if n_classes is not None and (not isinstance(n_classes, int) or n_classes < 1):
        raise ValueError("n_classes must be a positive integer when provided")

    arr = np.asarray(output)
    if kind == "probabilities":
        if arr.ndim != 2 or arr.shape[0] != n_rows:
            raise ValueError(
                "probabilities must have shape (n_rows, n_classes); "
                f"got {arr.shape} for n_rows={n_rows}"
            )
        if n_classes is not None and arr.shape[1] != n_classes:
            raise ValueError(
                f"expected {n_classes} probability columns, got {arr.shape[1]}"
            )
        numeric = np.asarray(arr, dtype=float)
        if not np.all(np.isfinite(numeric)):
            raise ValueError("probabilities contain non-finite values")
        if np.any(numeric < -1e-7) or np.any(numeric > 1.0 + 1e-7):
            raise ValueError("probabilities must lie in [0, 1]")
        if not np.allclose(numeric.sum(axis=1), 1.0, atol=1e-5):
            raise ValueError("each probability row must sum to one")
        return tuple(arr.shape)

    if kind == "scalar":
        valid_shape = (
            arr.ndim == 0 and n_rows == 1
        ) or (arr.ndim == 1 and arr.shape == (n_rows,)) or (
            arr.ndim == 2 and arr.shape == (n_rows, 1)
        )
        if not valid_shape:
            raise ValueError(
                "scalar output must have shape (), (n_rows,), or (n_rows, 1); "
                f"got {arr.shape} for n_rows={n_rows}"
            )
    elif kind == "scores":
        if arr.ndim not in (1, 2) or arr.shape[0] != n_rows:
            raise ValueError(
                "scores must have shape (n_rows,) or (n_rows, n_outputs); "
                f"got {arr.shape} for n_rows={n_rows}"
            )
    else:  # labels
        if not ((arr.ndim == 1 and arr.shape == (n_rows,)) or
                (arr.ndim == 2 and arr.shape == (n_rows, 1))):
            raise ValueError(
                "labels must have shape (n_rows,) or (n_rows, 1); "
                f"got {arr.shape} for n_rows={n_rows}"
            )
        numeric = np.asarray(arr, dtype=float)
        if not np.all(np.isfinite(numeric)):
            raise ValueError("labels contain non-finite values")
        if not np.allclose(numeric, np.round(numeric)):
            raise ValueError("labels must be integer-like")
        if n_classes is not None and (
            np.any(numeric < 0) or np.any(numeric >= n_classes)
        ):
            raise ValueError("labels fall outside [0, n_classes)")

    if kind in ("scalar", "scores"):
        try:
            numeric = np.asarray(arr, dtype=float)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{kind} output must be numeric") from exc
        if not np.all(np.isfinite(numeric)):
            raise ValueError(f"{kind} output contains non-finite values")
    return tuple(arr.shape)


def _fixture(kind: str, rows: int, classes: Optional[int]) -> Any:
    if kind == "probabilities":
        c = classes or 2
        out = np.zeros((rows, c), dtype=float)
        out[:, 0] = 1.0
        if c > 1:
            out[:, 0] = 0.75
            out[:, 1] = 0.25
        return out
    if kind == "labels":
        return np.arange(rows, dtype=int) % (classes or 2)
    if kind == "scalar":
        return np.linspace(0.0, 1.0, rows)
    return np.arange(rows * (classes or 2), dtype=float).reshape(rows, classes or 2)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate LIME, SHAP, GroupedCE, or NN output shapes."
    )
    parser.add_argument("--kind", choices=KINDS, required=True)
    parser.add_argument("--rows", type=int, required=True, help="input batch size")
    parser.add_argument("--classes", type=int, help="expected probability/label class count")
    parser.add_argument(
        "--values",
        help="optional JSON array/scalar to validate instead of the built-in fixture",
    )
    args = parser.parse_args()
    try:
        values = json.loads(args.values) if args.values is not None else _fixture(
            args.kind, args.rows, args.classes
        )
        shape = validate_model_output(
            values, args.rows, kind=args.kind, n_classes=args.classes
        )
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print(json.dumps({"valid": True, "kind": args.kind, "shape": list(shape)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
