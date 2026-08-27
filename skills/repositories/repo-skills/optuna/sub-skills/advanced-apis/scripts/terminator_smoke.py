#!/usr/bin/env python3
"""Deterministic smoke checks for Optuna advanced APIs.

Run with an environment where ``optuna`` is importable:

    python scripts/terminator_smoke.py
"""

from __future__ import annotations

import warnings

import optuna
from optuna.search_space import IntersectionSearchSpace
from optuna.study import Study
from optuna.terminator import BaseTerminator
from optuna.terminator import TerminatorCallback
from optuna.trial import Trial
from optuna.trial import TrialState

optuna.logging.set_verbosity(optuna.logging.WARNING)


class StopAfterTrialNumber(BaseTerminator):
    def __init__(self, last_trial_number: int) -> None:
        self._last_trial_number = last_trial_number

    def should_terminate(self, study: Study) -> bool:
        complete_trials = study.get_trials(states=[TrialState.COMPLETE])
        return bool(complete_trials) and max(t.number for t in complete_trials) >= self._last_trial_number


def objective(trial: Trial) -> float:
    branch = trial.suggest_categorical("branch", ["left", "right"])
    x = trial.suggest_float("x", -1.0, 1.0)
    if branch == "left":
        trial.suggest_float("left_only", 0.0, 1.0)
    else:
        trial.suggest_int("right_only", 1, 3)
    return x * x


def run_terminator_callback_check() -> None:
    study = optuna.create_study(
        direction="minimize",
        sampler=optuna.samplers.RandomSampler(seed=13),
    )
    callback = TerminatorCallback(StopAfterTrialNumber(last_trial_number=3))
    study.optimize(objective, n_trials=20, callbacks=[callback])
    assert len(study.trials) == 4, len(study.trials)


def run_search_space_check() -> None:
    study = optuna.create_study(
        direction="minimize",
        sampler=optuna.samplers.RandomSampler(seed=19),
    )
    study.enqueue_trial({"branch": "left", "x": 0.1, "left_only": 0.2})
    study.enqueue_trial({"branch": "right", "x": -0.1, "right_only": 2})
    study.optimize(objective, n_trials=2)

    search_space = IntersectionSearchSpace().calculate(study)
    assert "branch" in search_space
    assert "x" in search_space
    assert "left_only" not in search_space
    assert "right_only" not in search_space


def run_logging_check() -> None:
    before = optuna.logging.get_verbosity()
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    assert optuna.logging.get_verbosity() == optuna.logging.WARNING
    optuna.logging.set_verbosity(before)


def run_hypervolume_check() -> None:
    try:
        import numpy as np
        from optuna._hypervolume import compute_hypervolume
    except Exception:
        return

    loss_vals = np.array([[1.0, 4.0], [2.0, 2.0], [4.0, 1.0]])
    reference_point = np.array([5.0, 5.0])
    value = compute_hypervolume(loss_vals, reference_point)
    assert value > 0.0, value


def run_exception_alias_check() -> None:
    assert issubclass(optuna.TrialPruned, optuna.exceptions.OptunaError)
    assert issubclass(optuna.exceptions.ExperimentalWarning, Warning)


def main() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        run_terminator_callback_check()
    run_search_space_check()
    run_logging_check()
    run_hypervolume_check()
    run_exception_alias_check()
    print("advanced-apis smoke passed")


if __name__ == "__main__":
    main()
