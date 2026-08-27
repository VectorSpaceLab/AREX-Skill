#!/usr/bin/env python3
"""One-hot encode categorical CSVs and write Kaggle-style logistic predictions."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


MISSING_TOKEN = "__missing__"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fit a sparse one-hot logistic model on a categorical CSV and write probabilities.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--train", required=True, type=Path, help="Training CSV with a label column.")
    parser.add_argument("--test", required=True, type=Path, help="Test CSV with the same feature columns.")
    parser.add_argument("--output", required=True, type=Path, help="Output submission CSV.")
    parser.add_argument("--label-column", default="ACTION", help="Training label column name.")
    parser.add_argument("--id-column", default="id", help="Row identifier column name.")
    parser.add_argument("--C", type=float, default=3.0, help="Logistic regression regularization strength.")
    parser.add_argument("--solver", default="liblinear", help="Logistic regression solver.")
    parser.add_argument("--max-iter", type=int, default=500, help="Upper bound on solver iterations.")
    parser.add_argument("--cv-splits", type=int, default=0, help="Bounded stratified CV folds; 0 disables CV.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for CV shuffling.")
    return parser


def load_table(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    if frame.empty:
        raise ValueError(f"{path} is empty")
    return frame


def resolve_feature_columns(frame: pd.DataFrame, label_column: str, id_column: str) -> list[str]:
    feature_columns = [column for column in frame.columns if column not in {label_column, id_column}]
    if not feature_columns:
        raise ValueError("No feature columns remain after removing label and id columns")
    return feature_columns


def normalize_features(frame: pd.DataFrame, feature_columns: list[str]) -> pd.DataFrame:
    normalized = frame.reindex(columns=feature_columns)
    normalized = normalized.astype("string").fillna(MISSING_TOKEN)
    return normalized


def build_pipeline(C: float, solver: str, max_iter: int, seed: int) -> Pipeline:
    encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=True)
    model = LogisticRegression(C=C, solver=solver, max_iter=max_iter, random_state=seed)
    return Pipeline([("encoder", encoder), ("model", model)])


def maybe_run_cv(pipeline: Pipeline, X: pd.DataFrame, y: np.ndarray, cv_splits: int, seed: int) -> None:
    if cv_splits <= 1:
        print("CV disabled.")
        return

    _, class_counts = np.unique(y, return_counts=True)
    if class_counts.size < 2 or class_counts.min() < 2:
        print("Skipping CV: not enough samples from both classes.")
        return

    splits = min(cv_splits, int(class_counts.min()))
    if splits < 2:
        print("Skipping CV: the bounded fold count collapsed below 2.")
        return

    splitter = StratifiedKFold(n_splits=splits, shuffle=True, random_state=seed)
    scores: list[float] = []
    for fold, (train_idx, valid_idx) in enumerate(splitter.split(X, y), start=1):
        fold_pipeline = clone(pipeline)
        fold_pipeline.fit(X.iloc[train_idx], y[train_idx])
        probabilities = fold_pipeline.predict_proba(X.iloc[valid_idx])[:, 1]
        try:
            score = roc_auc_score(y[valid_idx], probabilities)
        except ValueError as exc:
            print(f"Skipping fold {fold}: {exc}")
            continue
        scores.append(score)
        print(f"fold {fold}/{splits} ROC AUC: {score:.6f}")

    if scores:
        print(f"Mean CV ROC AUC: {float(np.mean(scores)):.6f}")
    else:
        print("No valid CV scores were produced.")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    train = load_table(args.train)
    test = load_table(args.test)

    if args.label_column not in train.columns:
        raise ValueError(f"Training CSV is missing required label column {args.label_column!r}")

    feature_columns = resolve_feature_columns(train, args.label_column, args.id_column)
    train_features = normalize_features(train, feature_columns)
    test_features = normalize_features(test, feature_columns)

    y = pd.to_numeric(train[args.label_column], errors="raise").astype(int).to_numpy()
    pipeline = build_pipeline(args.C, args.solver, args.max_iter, args.seed)

    maybe_run_cv(pipeline, train_features, y, args.cv_splits, args.seed)

    pipeline.fit(train_features, y)
    probabilities = pipeline.predict_proba(test_features)[:, 1]

    if args.id_column in test.columns:
        ids = test[args.id_column]
        id_header = args.id_column
    else:
        ids = np.arange(1, len(test) + 1)
        id_header = args.id_column or "id"

    output = pd.DataFrame({id_header: ids, args.label_column: probabilities})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(args.output, index=False, float_format="%.6f")
    print(f"Wrote {len(output)} predictions to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
