#!/usr/bin/env python3
"""Demonstrate leakage-safe PyDESeq2 median-of-ratios normalization.

The script fits normalization facts on a training count matrix and applies them
to held-out test counts with deseq2_norm_transform. It uses tiny in-memory data,
prints the fitted logmeans/filter mask and size factors, and performs no network
or filesystem writes.
"""

from __future__ import annotations

import argparse
import json
from typing import Any


def load_runtime_dependencies():
    """Import scientific dependencies only after argparse handles --help."""
    try:
        import numpy as np
        import pandas as pd
        from pydeseq2.preprocessing import deseq2_norm
        from pydeseq2.preprocessing import deseq2_norm_fit
        from pydeseq2.preprocessing import deseq2_norm_transform
    except ImportError as exc:  # pragma: no cover - helpful CLI failure path
        raise SystemExit(
            "PyDESeq2 and its scientific dependencies are not importable. Install "
            "them in the active environment with a generic command such as: "
            "python -m pip install pydeseq2"
        ) from exc

    return np, pd, deseq2_norm, deseq2_norm_fit, deseq2_norm_transform


def make_tiny_split() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return deterministic samples-by-genes train/test count matrices."""
    train = pd.DataFrame(
        {
            "gene_a": [80, 94, 130, 148],
            "gene_b": [36, 40, 74, 88],
            "gene_c": [210, 230, 180, 190],
            "gene_d": [15, 18, 35, 39],
        },
        index=["train_1", "train_2", "train_3", "train_4"],
    )
    test = pd.DataFrame(
        {
            "gene_a": [82, 152],
            "gene_b": [38, 91],
            "gene_c": [205, 184],
            "gene_d": [17, 41],
        },
        index=["test_1", "test_2"],
    )
    return train, test


def align_test_to_train(train: pd.DataFrame, test: pd.DataFrame) -> pd.DataFrame:
    """Ensure held-out counts have the same gene columns and order as training counts."""
    missing = list(train.columns.difference(test.columns))
    extra = list(test.columns.difference(train.columns))
    if missing or extra:
        raise ValueError(
            "Train/test gene columns differ. "
            f"Missing in test: {missing or '-'}; extra in test: {extra or '-'}"
        )
    return test.loc[:, train.columns]


def frame_to_rounded_dict(frame: pd.DataFrame, digits: int) -> dict[str, dict[str, float]]:
    return frame.round(digits).to_dict(orient="index")


def array_to_rounded_list(values: np.ndarray, digits: int) -> list[float]:
    return np.round(np.asarray(values, dtype=float), digits).tolist()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Fit PyDESeq2 median-of-ratios normalization on training counts "
            "and transform held-out counts without fitting on test samples."
        )
    )
    parser.add_argument(
        "--as-json",
        action="store_true",
        help="Emit a JSON payload instead of a readable report.",
    )
    parser.add_argument(
        "--round",
        type=int,
        default=4,
        help="Decimal places for printed numeric values; default: 4.",
    )
    parser.add_argument(
        "--show-full-matrices",
        action="store_true",
        help="Print normalized count matrices in addition to size factors.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    global np, pd, deseq2_norm, deseq2_norm_fit, deseq2_norm_transform
    np, pd, deseq2_norm, deseq2_norm_fit, deseq2_norm_transform = load_runtime_dependencies()
    train_counts, test_counts = make_tiny_split()
    test_counts = align_test_to_train(train_counts, test_counts)

    logmeans, filtered_genes = deseq2_norm_fit(train_counts)
    train_normed, train_size_factors = deseq2_norm_transform(
        train_counts, logmeans, filtered_genes
    )
    test_normed, test_size_factors = deseq2_norm_transform(
        test_counts, logmeans, filtered_genes
    )

    convenience_normed, convenience_size_factors = deseq2_norm(train_counts)
    max_train_difference = float(
        np.max(np.abs(train_normed.to_numpy() - convenience_normed.to_numpy()))
    )
    max_size_factor_difference = float(
        np.max(np.abs(np.asarray(train_size_factors) - np.asarray(convenience_size_factors)))
    )

    payload: dict[str, Any] = {
        "train_shape": list(train_counts.shape),
        "test_shape": list(test_counts.shape),
        "genes": list(train_counts.columns),
        "fit_on": "train_counts_only",
        "transform_on": ["train_counts", "test_counts"],
        "logmeans": array_to_rounded_list(logmeans, args.round),
        "filtered_genes": [bool(value) for value in filtered_genes],
        "train_size_factors": dict(
            zip(train_counts.index, array_to_rounded_list(train_size_factors, args.round), strict=True)
        ),
        "test_size_factors": dict(
            zip(test_counts.index, array_to_rounded_list(test_size_factors, args.round), strict=True)
        ),
        "max_train_normed_difference_vs_deseq2_norm": round(max_train_difference, args.round),
        "max_train_size_factor_difference_vs_deseq2_norm": round(max_size_factor_difference, args.round),
        "leakage_warning": (
            "Do not call deseq2_norm(test_counts) in a train/test modeling pipeline; "
            "that would fit logmeans on held-out samples."
        ),
    }

    if args.show_full_matrices or args.as_json:
        payload["train_normed_counts"] = frame_to_rounded_dict(train_normed, args.round)
        payload["test_normed_counts"] = frame_to_rounded_dict(test_normed, args.round)

    if args.as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return

    print("PyDESeq2 leakage-safe normalization check")
    print(f"train shape: {tuple(payload['train_shape'])}; test shape: {tuple(payload['test_shape'])}")
    print(f"genes: {', '.join(payload['genes'])}")
    print("fit: deseq2_norm_fit(train_counts)")
    print("transform: deseq2_norm_transform(train_or_test_counts, logmeans, filtered_genes)")
    print(f"logmeans: {payload['logmeans']}")
    print(f"filtered_genes: {payload['filtered_genes']}")
    print("train size factors:")
    for sample, value in payload["train_size_factors"].items():
        print(f"  {sample}: {value}")
    print("test size factors:")
    for sample, value in payload["test_size_factors"].items():
        print(f"  {sample}: {value}")
    print(
        "max difference versus deseq2_norm(train_counts): "
        f"normed={payload['max_train_normed_difference_vs_deseq2_norm']}, "
        f"size_factors={payload['max_train_size_factor_difference_vs_deseq2_norm']}"
    )
    print(f"warning: {payload['leakage_warning']}")

    if args.show_full_matrices:
        print("train normalized counts:")
        print(train_normed.round(args.round).to_string())
        print("test normalized counts:")
        print(test_normed.round(args.round).to_string())


if __name__ == "__main__":
    main()
