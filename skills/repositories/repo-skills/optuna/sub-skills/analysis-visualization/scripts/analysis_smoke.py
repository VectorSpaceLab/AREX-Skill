#!/usr/bin/env python3
"""Smoke checks for Optuna post-optimization analysis APIs."""

from __future__ import annotations

import importlib.util
import json
from typing import Any
import warnings

import optuna
from optuna.exceptions import ExperimentalWarning
from optuna.importance import PedAnovaImportanceEvaluator
from optuna.importance import get_param_importances


optuna.logging.set_verbosity(optuna.logging.WARNING)
warnings.filterwarnings("ignore", category=ExperimentalWarning)
warnings.filterwarnings("ignore", message="PedAnovaImportanceEvaluator computes.*", category=UserWarning)


def _make_study() -> optuna.study.Study:
    sampler = optuna.samplers.RandomSampler(seed=7)
    study = optuna.create_study(direction="minimize", sampler=sampler)

    def objective(trial: optuna.Trial) -> float:
        x = trial.suggest_float("x", -2.0, 2.0)
        y = trial.suggest_float("y", 0.0, 3.0)
        if trial.number % 2 == 0:
            trial.suggest_float("conditional", 0.0, 1.0)
        trial.set_user_attr("fold", trial.number % 2)
        return (x - 0.25) ** 2 + 0.1 * y

    study.optimize(objective, n_trials=10)
    return study


def _record(results: list[dict[str, Any]], name: str, status: str, detail: Any) -> None:
    results.append({"check": name, "status": status, "detail": detail})


def main() -> int:
    results: list[dict[str, Any]] = []
    study = _make_study()

    importances = get_param_importances(
        study,
        evaluator=PedAnovaImportanceEvaluator(),
        params=["x", "y"],
    )
    assert set(importances) == {"x", "y"}, importances
    assert all(value >= 0.0 for value in importances.values()), importances
    assert abs(sum(importances.values()) - 1.0) < 1e-9, importances
    _record(results, "ped_anova_importances", "passed", importances)

    multi = optuna.create_study(directions=["minimize", "maximize"], sampler=optuna.samplers.RandomSampler(seed=3))

    def multi_objective(trial: optuna.Trial) -> tuple[float, float]:
        x = trial.suggest_float("x", -1.0, 1.0)
        y = trial.suggest_float("y", -1.0, 1.0)
        return (x - 0.2) ** 2 + y**2, x - y

    multi.optimize(multi_objective, n_trials=8)
    first_objective_importances = get_param_importances(
        multi,
        evaluator=PedAnovaImportanceEvaluator(),
        params=["x", "y"],
        target=lambda trial: trial.values[0],
    )
    assert set(first_objective_importances) == {"x", "y"}, first_objective_importances
    _record(results, "multi_objective_target_importances", "passed", first_objective_importances)

    if importlib.util.find_spec("pandas") is None:
        _record(results, "trials_dataframe", "skipped", "pandas is not installed")
    else:
        dataframe = study.trials_dataframe(attrs=("number", "value", "params", "user_attrs", "state"))
        assert len(dataframe) == len(study.trials), dataframe
        assert "params_x" in dataframe.columns, list(dataframe.columns)
        _record(results, "trials_dataframe", "passed", {"rows": int(dataframe.shape[0]), "columns": list(map(str, dataframe.columns))})

    if importlib.util.find_spec("sklearn") is None:
        _record(results, "default_fanova_importances", "skipped", "scikit-learn is not installed")
    else:
        default_importances = get_param_importances(study, params=["x", "y"])
        assert set(default_importances) == {"x", "y"}, default_importances
        _record(results, "default_fanova_importances", "passed", default_importances)

    print(json.dumps({"status": "ok", "results": results}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
