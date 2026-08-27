#!/usr/bin/env python3
"""Create a tiny CellTypist-compatible model pickle for offline smoke tests."""

from __future__ import annotations

import argparse
import json
import pickle
import sys
from pathlib import Path
from typing import Dict, Optional, Sequence, Tuple

DEFAULT_CLASSES = ("type_alpha", "type_beta")


def make_counts(cell_count: int, gene_count: int, seed: int):
    import numpy as np
    import pandas as pd

    rng = np.random.default_rng(seed)
    genes = [f"GENE{index:02d}" for index in range(gene_count)]
    cells = [f"cell_{index:03d}" for index in range(cell_count)]
    split_index = cell_count // 2
    labels = np.array([DEFAULT_CLASSES[0]] * split_index + [DEFAULT_CLASSES[1]] * (cell_count - split_index))

    counts = rng.poisson(lam=1.0, size=(cell_count, gene_count)).astype(int)
    alpha_width = max(2, gene_count // 2)
    beta_start = min(alpha_width, gene_count - 2)
    counts[:split_index, :alpha_width] += rng.poisson(lam=7.0, size=(split_index, alpha_width))
    counts[split_index:, beta_start:] += rng.poisson(lam=7.0, size=(cell_count - split_index, gene_count - beta_start))
    counts += 1
    return pd.DataFrame(counts, index=cells, columns=genes), labels


def normalize_log1p(counts_frame):
    import numpy as np

    counts = counts_frame.to_numpy(dtype=float)
    totals = counts.sum(axis=1, keepdims=True)
    normalized = counts / totals * 10000.0
    return np.log1p(normalized)


def fit_model(counts_frame, labels, max_iter: int):
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    expression = normalize_log1p(counts_frame)
    scaler = StandardScaler()
    scaled_expression = scaler.fit_transform(expression)
    classifier = LogisticRegression(max_iter=max_iter, solver="lbfgs")
    classifier.fit(scaled_expression, labels)
    classifier.features = counts_frame.columns.astype(str).to_numpy()
    classifier.n_features_in_ = len(classifier.features)
    return classifier, scaler


def write_model(path: Path, classifier, scaler) -> Path:
    output_path = path.with_suffix(".pkl")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "Model": classifier,
        "Scaler_": scaler,
        "description": {
            "date": "synthetic-offline-fixture",
            "details": "Tiny synthetic CellTypist-compatible smoke-test model; not for biological interpretation.",
            "url": "",
            "source": "synthetic",
            "version": "1",
            "number_celltypes": int(len(classifier.classes_)),
        },
    }
    with output_path.open("wb") as handle:
        pickle.dump(payload, handle)
    return output_path


def write_query(path: Path, counts_frame) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    counts_frame.to_csv(path)
    return path


def inspect_written_model(path: Path) -> Dict[str, object]:
    with path.open("rb") as handle:
        payload = pickle.load(handle)
    classifier = payload["Model"]
    scaler = payload["Scaler_"]
    return {
        "path": str(path),
        "classes": [str(value) for value in classifier.classes_],
        "feature_count": int(len(classifier.features)),
        "feature_preview": [str(value) for value in classifier.features[:8]],
        "coef_shape": list(classifier.coef_.shape),
        "scaler_feature_count": int(len(scaler.mean_)),
        "description": payload["description"],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Create a tiny sklearn LogisticRegression + StandardScaler pickle with the CellTypist "
            "Model.load() dictionary layout. No network access or CellTypist import is required."
        )
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("tiny_celltypist_model.pkl"),
        help="Output model pickle path. The suffix is forced to .pkl. Default: tiny_celltypist_model.pkl.",
    )
    parser.add_argument(
        "--cells",
        type=int,
        default=60,
        help="Number of synthetic training cells. Must be at least 4. Default: 60.",
    )
    parser.add_argument(
        "--genes",
        type=int,
        default=8,
        help="Number of synthetic genes/features. Must be at least 4. Default: 8.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=17,
        help="Random seed for reproducible synthetic counts. Default: 17.",
    )
    parser.add_argument(
        "--max-iter",
        type=int,
        default=200,
        help="LogisticRegression max_iter. Default: 200.",
    )
    parser.add_argument(
        "--write-query-csv",
        type=Path,
        help="Optional path for a matching raw count CSV query fixture with the same genes.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON summary instead of a text summary.",
    )
    return parser


def validate_args(args: argparse.Namespace) -> None:
    if args.cells < 4:
        raise SystemExit("--cells must be at least 4 so both synthetic classes have examples")
    if args.genes < 4:
        raise SystemExit("--genes must be at least 4 so both synthetic signatures have features")
    if args.max_iter <= 0:
        raise SystemExit("--max-iter must be positive")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    validate_args(args)

    counts_frame, labels = make_counts(args.cells, args.genes, args.seed)
    classifier, scaler = fit_model(counts_frame, labels, args.max_iter)
    output_path = write_model(args.output, classifier, scaler)
    summary = inspect_written_model(output_path)
    summary["network_used"] = False
    summary["celltypist_imported"] = False

    if args.write_query_csv is not None:
        summary["query_csv"] = str(write_query(args.write_query_csv, counts_frame))

    if args.json:
        json.dump(summary, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        print(f"wrote model: {summary['path']}")
        print(f"classes: {', '.join(summary['classes'])}")
        print(f"features: {summary['feature_count']} ({', '.join(summary['feature_preview'])})")
        if "query_csv" in summary:
            print(f"wrote query csv: {summary['query_csv']}")
        print("network used: false")
        print("celltypist imported: false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
