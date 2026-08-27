#!/usr/bin/env python3
"""Smoke checks for Optuna visualization APIs with optional backend skips."""

from __future__ import annotations

import importlib.util
import json
from typing import Any
import warnings

import optuna
from optuna.exceptions import ExperimentalWarning
from optuna.importance import PedAnovaImportanceEvaluator


optuna.logging.set_verbosity(optuna.logging.WARNING)
warnings.filterwarnings("ignore", category=ExperimentalWarning)


def _record(results: list[dict[str, Any]], name: str, status: str, detail: Any) -> None:
    results.append({"check": name, "status": status, "detail": detail})


def _make_single_objective_study() -> optuna.study.Study:
    study = optuna.create_study(direction="minimize", sampler=optuna.samplers.RandomSampler(seed=11))

    def objective(trial: optuna.Trial) -> float:
        x = trial.suggest_float("x", -2.0, 2.0)
        y = trial.suggest_float("y", 0.0, 2.0)
        for step in range(3):
            trial.report((x - 0.5) ** 2 + y / (step + 1), step)
        return (x - 0.5) ** 2 + 0.25 * y

    study.optimize(objective, n_trials=8)
    return study


def _make_multi_objective_study() -> optuna.study.Study:
    study = optuna.create_study(directions=["minimize", "maximize"], sampler=optuna.samplers.RandomSampler(seed=13))

    def objective(trial: optuna.Trial) -> tuple[float, float]:
        x = trial.suggest_float("x", -1.0, 1.0)
        y = trial.suggest_float("y", -1.0, 1.0)
        return (x - 0.1) ** 2 + y**2, 1.0 - abs(x + y)

    study.optimize(objective, n_trials=8)
    study.set_metric_names(["loss", "score"])
    return study


def _check_plotly(single: optuna.study.Study, multi: optuna.study.Study, results: list[dict[str, Any]]) -> None:
    if importlib.util.find_spec("plotly") is None:
        _record(results, "plotly_backend", "skipped", "plotly is not installed")
        return

    from optuna.visualization import plot_hypervolume_history
    from optuna.visualization import plot_optimization_history
    from optuna.visualization import plot_param_importances
    from optuna.visualization import plot_pareto_front
    from optuna.visualization import plot_slice

    history = plot_optimization_history(single)
    slice_plot = plot_slice(single, params=["x", "y"])
    importances = plot_param_importances(
        single,
        evaluator=PedAnovaImportanceEvaluator(),
        params=["x", "y"],
        target_name="Loss",
    )
    pareto = plot_pareto_front(multi, target_names=["loss", "score"])
    hypervolume = plot_hypervolume_history(multi, reference_point=[5.0, -1.0])

    _record(
        results,
        "plotly_backend",
        "passed",
        {
            "history_traces": len(history.data),
            "slice_traces": len(slice_plot.data),
            "importance_traces": len(importances.data),
            "pareto_traces": len(pareto.data),
            "hypervolume_traces": len(hypervolume.data),
        },
    )


def _check_matplotlib(single: optuna.study.Study, multi: optuna.study.Study, results: list[dict[str, Any]]) -> None:
    if importlib.util.find_spec("matplotlib") is None:
        _record(results, "matplotlib_backend", "skipped", "matplotlib is not installed")
        return

    from optuna.visualization.matplotlib import plot_hypervolume_history
    from optuna.visualization.matplotlib import plot_optimization_history
    from optuna.visualization.matplotlib import plot_param_importances
    from optuna.visualization.matplotlib import plot_pareto_front
    from optuna.visualization.matplotlib import plot_slice

    history_ax = plot_optimization_history(single)
    slice_axes = plot_slice(single, params=["x", "y"])
    importance_ax = plot_param_importances(
        single,
        evaluator=PedAnovaImportanceEvaluator(),
        params=["x", "y"],
        target_name="Loss",
    )
    pareto_ax = plot_pareto_front(multi, target_names=["loss", "score"])
    hypervolume_ax = plot_hypervolume_history(multi, reference_point=[5.0, -1.0])

    _record(
        results,
        "matplotlib_backend",
        "passed",
        {
            "history_type": type(history_ax).__name__,
            "slice_type": type(slice_axes).__name__,
            "importance_type": type(importance_ax).__name__,
            "pareto_type": type(pareto_ax).__name__,
            "hypervolume_type": type(hypervolume_ax).__name__,
        },
    )


def main() -> int:
    results: list[dict[str, Any]] = []
    single = _make_single_objective_study()
    multi = _make_multi_objective_study()

    _check_plotly(single, multi, results)
    _check_matplotlib(single, multi, results)

    print(json.dumps({"status": "ok", "results": results}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
