#!/usr/bin/env python3
"""Deterministic smoke checks for Optuna samplers and pruners.

This script intentionally uses only Optuna plus NumPy-backed standard behavior.
Optional algorithms are probed and reported as skipped when their optional
runtime dependencies are absent.
"""

from __future__ import annotations

import importlib.util
import json
from typing import Any
import warnings

import optuna
from optuna.trial import TrialState


warnings.filterwarnings("ignore", category=optuna.exceptions.ExperimentalWarning)
optuna.logging.set_verbosity(optuna.logging.WARNING)


def _objective_with_pruning(trial: optuna.Trial) -> float:
    optimizer = trial.suggest_categorical("optimizer", ["adam", "sgd"])
    learning_rate = trial.suggest_float("learning_rate", 1e-3, 1e-1, log=True)
    depth = trial.suggest_int("depth", 1, 3)

    optimizer_penalty = 0.0 if optimizer == "adam" else 0.05
    target = (learning_rate - 0.02) ** 2 + 0.01 * (depth - 2) ** 2 + optimizer_penalty
    for step in range(4):
        intermediate = target + 0.03 / (step + 1)
        trial.report(intermediate, step)
        if trial.should_prune():
            raise optuna.TrialPruned()
    return target


def run_tpe_hyperband() -> dict[str, Any]:
    sampler = optuna.samplers.TPESampler(
        seed=7,
        multivariate=True,
        group=True,
        constant_liar=True,
    )
    pruner = optuna.pruners.HyperbandPruner(
        min_resource=1,
        max_resource=4,
        reduction_factor=2,
    )
    study = optuna.create_study(
        direction="minimize",
        sampler=sampler,
        pruner=pruner,
        study_name="sampler-pruner-smoke-tpe-hyperband",
    )
    study.optimize(_objective_with_pruning, n_trials=12)
    states = {state.name: 0 for state in TrialState}
    for trial in study.trials:
        states[trial.state.name] += 1
    assert states["COMPLETE"] >= 1
    assert study.best_trial.params["optimizer"] in {"adam", "sgd"}
    return {
        "best_value": round(float(study.best_value), 8),
        "best_params": study.best_trial.params,
        "states": {key: value for key, value in states.items() if value},
    }


def run_grid_exhaustion() -> dict[str, Any]:
    search_space = {
        "optimizer": ["adam", "sgd"],
        "learning_rate": [0.01, 0.1],
    }
    sampler = optuna.samplers.GridSampler(search_space, seed=3)
    study = optuna.create_study(
        direction="minimize",
        sampler=sampler,
        study_name="sampler-pruner-smoke-grid",
    )

    def objective(trial: optuna.Trial) -> float:
        optimizer = trial.suggest_categorical("optimizer", search_space["optimizer"])
        learning_rate = trial.suggest_float("learning_rate", 0.01, 0.1)
        return (learning_rate - 0.01) ** 2 + (0.0 if optimizer == "adam" else 0.1)

    study.optimize(objective)
    assert len(study.trials) == 4
    assert sampler.is_exhausted(study)
    return {"trials": len(study.trials), "exhausted": sampler.is_exhausted(study)}


def probe_optional_algorithms() -> dict[str, str]:
    probes: dict[str, tuple[str, Any]] = {
        "cmaes": ("cmaes", lambda: optuna.samplers.CmaEsSampler(seed=0)),
        "qmc": ("scipy", lambda: optuna.samplers.QMCSampler(seed=0)),
        "wilcoxon": ("scipy", lambda: optuna.pruners.WilcoxonPruner(p_threshold=0.1)),
        "gp": ("torch", lambda: optuna.samplers.GPSampler(seed=0)),
    }
    results: dict[str, str] = {}
    for name, (module_name, factory) in probes.items():
        if importlib.util.find_spec(module_name) is None:
            results[name] = f"skipped: optional dependency {module_name!r} is not installed"
            continue
        try:
            factory()
        except Exception as exc:  # pragma: no cover - reports environment-specific incompatibility.
            results[name] = f"available dependency but construction failed: {type(exc).__name__}: {exc}"
        else:
            results[name] = "constructed"
    return results


def main() -> None:
    result = {
        "optuna_version": optuna.__version__,
        "tpe_hyperband": run_tpe_hyperband(),
        "grid_exhaustion": run_grid_exhaustion(),
        "optional_algorithms": probe_optional_algorithms(),
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
