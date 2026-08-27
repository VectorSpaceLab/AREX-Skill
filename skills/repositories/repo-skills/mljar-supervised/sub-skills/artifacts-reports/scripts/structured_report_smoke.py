#!/usr/bin/env python3
"""Tiny structured-report smoke helper for mljar-supervised.

The helper trains a very small synthetic AutoML run with explain_level=0,
reloads it from results_path, calls report_structured in markdown/dict/json
formats, optionally requests a model-specific report, and prints stable signals.
It is safe by default: without --output it uses a temporary directory that is
removed on exit; with --output it refuses to overwrite non-empty directories
unless --overwrite is supplied.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Train a tiny synthetic mljar-supervised AutoML run and verify "
            "structured report, reload, and prediction-after-load signals."
        )
    )
    parser.add_argument(
        "--task",
        choices=["classification", "regression"],
        default="classification",
        help="Synthetic task to train. Default: classification.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=(
            "Optional results_path directory. If omitted, a temporary directory "
            "is used and cleaned up."
        ),
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help=(
            "Replace an existing AutoML-like output directory. Refuses to remove "
            "directories that do not look like previous AutoML outputs."
        ),
    )
    parser.add_argument(
        "--model-name",
        default=None,
        help=(
            "Optional exact model name for report_structured(model_name=...). "
            "If omitted, the first leaderboard model is used."
        ),
    )
    parser.add_argument(
        "--n-samples",
        type=int,
        default=80,
        help="Number of synthetic rows. Must be at least 40. Default: 80.",
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=123,
        help="Random seed for synthetic data and AutoML. Default: 123.",
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="When --output is omitted, keep the temporary directory for inspection.",
    )
    return parser.parse_args(argv)


def looks_like_automl_output(path: Path) -> bool:
    markers = {
        "params.json",
        "leaderboard.csv",
        "README.md",
        "README.html",
        "report_structured.json",
        "errors.md",
        "data_info.json",
    }
    try:
        names = {child.name for child in path.iterdir()}
    except OSError:
        return False
    return bool(names & markers) or path.name.startswith("AutoML")


def prepare_output_dir(path: Path, overwrite: bool) -> Path:
    resolved = path.expanduser().resolve()
    if resolved in {Path(resolved.anchor), Path.home().resolve()}:
        raise SystemExit(f"Refusing dangerous output directory: {resolved}")
    if resolved.exists() and not resolved.is_dir():
        raise SystemExit(f"Output exists and is not a directory: {resolved}")
    if resolved.exists():
        has_contents = any(resolved.iterdir())
        if has_contents and not overwrite:
            raise SystemExit(
                f"Output directory is not empty: {resolved}. "
                "Use --overwrite for an AutoML output you intend to replace."
            )
        if has_contents and overwrite:
            if not looks_like_automl_output(resolved):
                raise SystemExit(
                    f"Refusing to remove directory that does not look like an AutoML output: {resolved}"
                )
            shutil.rmtree(resolved)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return resolved


def make_data(task: str, n_samples: int, random_state: int) -> tuple[Any, Any]:
    if n_samples < 40:
        raise SystemExit("--n-samples must be at least 40 for stable validation splits")

    import pandas as pd
    from sklearn.datasets import make_classification, make_regression

    if task == "classification":
        X, y = make_classification(
            n_samples=n_samples,
            n_features=6,
            n_informative=4,
            n_redundant=0,
            n_repeated=0,
            n_classes=2,
            n_clusters_per_class=1,
            random_state=random_state,
        )
    else:
        X, y = make_regression(
            n_samples=n_samples,
            n_features=6,
            n_informative=4,
            noise=1.0,
            random_state=random_state,
        )
    columns = [f"feature_{i}" for i in range(X.shape[1])]
    return pd.DataFrame(X, columns=columns), y


def frames_match(left: Any, right: Any) -> bool:
    import numpy as np

    if list(left.columns) != list(right.columns) or left.shape != right.shape:
        return False
    for column in left.columns:
        a = left[column].to_numpy()
        b = right[column].to_numpy()
        if np.issubdtype(a.dtype, np.number) and np.issubdtype(b.dtype, np.number):
            if not np.allclose(a, b, equal_nan=True):
                return False
        else:
            if list(a) != list(b):
                return False
    return True


def run_smoke(args: argparse.Namespace, results_path: Path) -> int:
    try:
        from supervised import AutoML
    except Exception as exc:  # pragma: no cover - environment-specific import failure
        print(
            "import_error=1\n"
            f"import_error_type={type(exc).__name__}\n"
            f"import_error_message={exc}",
            file=sys.stderr,
        )
        return 2

    X, y = make_data(args.task, args.n_samples, args.random_state)
    X_check = X.head(8).copy()

    automl = AutoML(
        results_path=str(results_path),
        mode="Explain",
        algorithms=["Baseline"],
        explain_level=0,
        train_ensemble=False,
        stack_models=False,
        validation_strategy={
            "validation_type": "split",
            "train_ratio": 0.75,
            "shuffle": True,
            "stratify": args.task == "classification",
            "random_seed": args.random_state,
        },
        total_time_limit=30,
        random_state=args.random_state,
        verbose=0,
    )
    automl.fit(X, y)

    before = automl.predict_all(X_check)
    loaded = AutoML(results_path=str(results_path))
    after = loaded.predict_all(X_check)
    same_after_load = frames_match(before, after)

    markdown = loaded.report_structured(format="markdown")
    compact = loaded.report_structured(format="dict")
    json_text = loaded.report_structured(format="json")
    parsed = json.loads(json_text)

    leaderboard = compact.get("leaderboard", [])
    selected_model = args.model_name
    if selected_model is None and leaderboard:
        selected_model = leaderboard[0].get("name")

    selected_keys: list[str] = []
    if selected_model:
        selected_payload = loaded.report_structured(format="dict", model_name=selected_model)
        selected_keys = sorted((selected_payload.get("selected_model") or {}).keys())

    report_json = results_path / "report_structured.json"

    print(f"task={args.task}")
    print(f"n_samples={args.n_samples}")
    print(f"leaderboard_rows={len(leaderboard)}")
    print("leaderboard_names=" + ",".join(str(row.get("name")) for row in leaderboard))
    print(f"prediction_after_load_equal={int(same_after_load)}")
    print(f"markdown_has_title={int('# MLJAR AutoML Report' in markdown)}")
    print("dict_keys=" + ",".join(sorted(compact.keys())))
    print(f"json_parse_ok={int(isinstance(parsed, dict) and 'leaderboard' in parsed)}")
    print(f"report_structured_json_exists={int(report_json.exists())}")
    if selected_model:
        print(f"selected_model_name={selected_model}")
        print("selected_model_keys=" + ",".join(selected_keys))
    print(f"output_kept={int(args.output is not None or args.keep_temp)}")

    return 0 if same_after_load and report_json.exists() else 1


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.output is not None:
        results_path = prepare_output_dir(args.output, args.overwrite)
        return run_smoke(args, results_path)

    tmp_parent = tempfile.mkdtemp(prefix="mljar_structured_report_")
    results_path = Path(tmp_parent) / "AutoML_structured_report_smoke"
    try:
        return run_smoke(args, results_path)
    finally:
        if args.keep_temp:
            print(f"kept_temp_dir={tmp_parent}")
        else:
            shutil.rmtree(tmp_parent, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
