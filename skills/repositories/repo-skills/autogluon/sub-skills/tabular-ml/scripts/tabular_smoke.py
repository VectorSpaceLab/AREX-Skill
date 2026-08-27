#!/usr/bin/env python3
"""Run a tiny, network-free AutoGluon Tabular smoke test."""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path


def build_data():
    import pandas as pd

    train = pd.DataFrame(
        {
            "age": [22, 25, 47, 52, 46, 56, 23, 31, 41, 35, 61, 29, 44, 38, 27, 50],
            "income": [35, 42, 88, 93, 78, 110, 36, 55, 72, 65, 120, 49, 83, 70, 45, 98],
            "segment": ["new", "new", "vip", "vip", "vip", "vip", "new", "mid", "mid", "mid", "vip", "new", "mid", "mid", "new", "vip"],
            "note": [
                "asked for discount",
                "first purchase",
                "priority support",
                "renewal call",
                "bulk buyer",
                "account expansion",
                "trial user",
                "newsletter click",
                "webinar attendee",
                "email reply",
                "executive sponsor",
                "cart recovery",
                "sales assisted",
                "repeat buyer",
                "coupon user",
                "enterprise lead",
            ],
            "converted": [0, 0, 1, 1, 1, 1, 0, 0, 1, 0, 1, 0, 1, 1, 0, 1],
        }
    )
    test = train.sample(frac=1.0, random_state=7).reset_index(drop=True)
    return train, test


def parse_hyperparameters(args):
    if args.model_family == "rf_xt":
        return {
            "RF": {"n_estimators": args.n_estimators, "ag_args": {"name_suffix": "Smoke"}},
            "XT": {"n_estimators": args.n_estimators, "ag_args": {"name_suffix": "Smoke"}},
        }
    if args.model_family == "rf":
        return {"RF": {"n_estimators": args.n_estimators, "ag_args": {"name_suffix": "Smoke"}}}
    if args.model_family == "xt":
        return {"XT": {"n_estimators": args.n_estimators, "ag_args": {"name_suffix": "Smoke"}}}
    raise ValueError(f"Unknown model family: {args.model_family}")


def run_smoke(args):
    from autogluon.tabular import TabularPredictor

    train, test = build_data()
    output_dir = Path(args.output_dir) if args.output_dir else Path(tempfile.mkdtemp(prefix="ag-tabular-smoke-"))
    output_dir = output_dir.expanduser().resolve()
    if output_dir.exists() and any(output_dir.iterdir()) and not args.allow_existing_output_dir:
        raise SystemExit(f"Output directory is not empty: {output_dir}. Use --allow-existing-output-dir to reuse it.")
    output_dir.mkdir(parents=True, exist_ok=True)

    predictor = TabularPredictor(
        label="converted",
        problem_type="binary",
        eval_metric=args.eval_metric,
        path=str(output_dir),
        verbosity=args.verbosity,
    ).fit(
        train,
        hyperparameters=parse_hyperparameters(args),
        time_limit=args.time_limit,
        num_cpus=args.num_cpus,
        num_gpus=0,
        fit_weighted_ensemble=args.fit_weighted_ensemble,
        presets=args.presets,
    )

    metrics = predictor.evaluate(test, auxiliary_metrics=True)
    leaderboard = predictor.leaderboard(test, skip_score=False)
    predictions = predictor.predict(test.drop(columns=["converted"])).astype(str).tolist()
    predictor.save(silent=True)
    loaded = TabularPredictor.load(str(output_dir), verbosity=args.verbosity, check_packages=args.check_packages)
    loaded_predictions = loaded.predict(test.drop(columns=["converted"])).astype(str).tolist()

    summary = {
        "ok": predictions == loaded_predictions,
        "path": str(output_dir),
        "problem_type": predictor.problem_type,
        "eval_metric": predictor.eval_metric.name,
        "model_count": len(predictor.model_names()),
        "model_best": predictor.model_best,
        "leaderboard_columns": list(leaderboard.columns),
        "metrics": {key: float(value) for key, value in metrics.items()},
        "predictions_match_after_load": predictions == loaded_predictions,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))

    if args.cleanup:
        shutil.rmtree(output_dir, ignore_errors=True)

    if not summary["ok"]:
        raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", help="Directory for predictor artifacts. Defaults to a temporary directory.")
    parser.add_argument("--allow-existing-output-dir", action="store_true", help="Allow writing into a non-empty output directory.")
    parser.add_argument("--cleanup", action="store_true", help="Delete the output directory after a successful run.")
    parser.add_argument("--time-limit", type=float, default=30.0, help="Training time limit in seconds.")
    parser.add_argument("--num-cpus", type=int, default=1, help="CPU count to pass to TabularPredictor.fit.")
    parser.add_argument("--verbosity", type=int, default=0, choices=range(0, 5), help="AutoGluon verbosity level.")
    parser.add_argument("--eval-metric", default="accuracy", help="Evaluation metric for the binary smoke task.")
    parser.add_argument("--presets", default=None, help="Optional AutoGluon presets value to pass through.")
    parser.add_argument("--model-family", choices=["rf_xt", "rf", "xt"], default="rf_xt", help="Lightweight built-in model family selection.")
    parser.add_argument("--n-estimators", type=int, default=20, help="Tree count for RF/XT smoke models.")
    parser.add_argument("--fit-weighted-ensemble", action="store_true", help="Also fit AutoGluon's weighted ensemble.")
    parser.add_argument("--check-packages", action="store_true", help="Check package metadata when reloading the predictor.")
    args = parser.parse_args()
    run_smoke(args)


if __name__ == "__main__":
    main()
