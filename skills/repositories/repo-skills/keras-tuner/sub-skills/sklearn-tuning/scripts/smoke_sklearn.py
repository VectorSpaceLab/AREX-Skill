#!/usr/bin/env python3
"""Run a bounded SklearnTuner check on a local synthetic fixture.

Safe by default: no network, no external datasets, and no writes outside a
caller-selected work directory (or a temporary directory that is cleaned up).
The fixture exercises conditional estimator branches, explicit scoring,
group-aware CV, sample weights, and pickle-backed model restoration.
"""

from __future__ import annotations

import argparse
import pathlib
import pickle
import sys
import tempfile

import numpy as np


def _add_repo_root(repo_root: str | None) -> None:
    if not repo_root:
        return
    repo = pathlib.Path(repo_root).resolve()
    if str(repo) not in sys.path:
        sys.path.insert(0, str(repo))


def _build_model(hp):
    from sklearn import ensemble, linear_model

    family = hp.Choice("family", ["logistic", "tree"])
    if family == "logistic":
        with hp.conditional_scope("family", "logistic"):
            return linear_model.LogisticRegression(
                C=hp.Float("C", 0.25, 1.0, step=0.75),
                max_iter=200,
                random_state=0,
            )
    with hp.conditional_scope("family", "tree"):
        return ensemble.RandomForestClassifier(
            n_estimators=hp.Int("n_estimators", 4, 8, step=4),
            max_depth=hp.Int("max_depth", 2, 3),
            random_state=0,
        )


def _fixture() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.RandomState(0)
    x = rng.normal(size=(24, 4))
    # Every group contains both classes, so GroupKFold remains valid for both
    # conditional estimator branches.
    y = np.tile(np.array([0, 1, 0, 1]), 6)
    groups = np.repeat(np.arange(6), 4)
    sample_weight = np.linspace(0.5, 1.5, num=len(y))
    return x, y, groups, sample_weight


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", help="Optional local checkout to add to sys.path.")
    parser.add_argument(
        "--workdir",
        help="Optional directory for tuner artifacts. Defaults to a temporary directory.",
    )
    args = parser.parse_args()
    _add_repo_root(args.repo_root)

    try:
        import keras_tuner as kt
        from sklearn import metrics, model_selection
    except ImportError as exc:
        print(f"Missing smoke-test dependency: {exc}", file=sys.stderr)
        return 2

    x, y, groups, sample_weight = _fixture()
    workdir_ctx = None
    if args.workdir:
        workdir = str(pathlib.Path(args.workdir).resolve())
        pathlib.Path(workdir).mkdir(parents=True, exist_ok=True)
    else:
        workdir_ctx = tempfile.TemporaryDirectory(prefix="keras-tuner-sklearn-smoke-")
        workdir = workdir_ctx.name

    try:
        oracle = kt.oracles.BayesianOptimizationOracle(
            objective=kt.Objective("score", "max"), max_trials=2, seed=0
        )
        tuner = kt.SklearnTuner(
            oracle=oracle,
            hypermodel=_build_model,
            scoring=metrics.make_scorer(metrics.accuracy_score),
            metrics=metrics.accuracy_score,
            cv=model_selection.GroupKFold(n_splits=3),
            directory=workdir,
            project_name="sklearn-smoke",
            overwrite=False,
        )
        tuner.search(x, y, sample_weight=sample_weight, groups=groups)

        best_trial = tuner.oracle.get_best_trials(1)[0]
        if best_trial.status != "COMPLETED":
            raise AssertionError(f"best trial did not complete: {best_trial.status}")
        if not best_trial.metrics.exists("score"):
            raise AssertionError("score metric was not recorded")
        if not np.isfinite(best_trial.score):
            raise AssertionError(f"non-finite score: {best_trial.score}")

        best_model = tuner.get_best_models(num_models=1)[0]
        if not hasattr(best_model, "predict"):
            raise AssertionError("restored object is not an estimator")
        predictions = best_model.predict(x)
        if len(predictions) != len(y):
            raise AssertionError("restored estimator returned the wrong row count")

        trial_dir = pathlib.Path(tuner.get_trial_dir(best_trial.trial_id))
        model_path = trial_dir / "model.pickle"
        if not model_path.is_file():
            raise AssertionError(f"missing pickle artifact: {model_path}")
        with model_path.open("rb") as handle:
            restored = pickle.load(handle)
        if not hasattr(restored, "score"):
            raise AssertionError("pickle artifact did not restore an estimator")

        print(f"trials={len(tuner.oracle.trials)}")
        print(f"best_family={best_trial.hyperparameters.values.get('family')}")
        print(f"best_score={best_trial.score:.6f}")
        print(f"pickle={model_path}")
        return 0
    finally:
        if workdir_ctx is not None:
            workdir_ctx.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
