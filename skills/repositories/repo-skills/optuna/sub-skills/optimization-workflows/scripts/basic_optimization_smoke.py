#!/usr/bin/env python3
"""Deterministic Optuna basic optimization smoke test.

Adapted from Optuna's first tutorial into a short, dependency-light script with assertions.
"""

from __future__ import annotations

import optuna


def objective(trial: optuna.Trial) -> float:
    x = trial.suggest_float("x", -10.0, 10.0)
    y = trial.suggest_int("y", -3, 3)
    trial.set_user_attr("branch", "positive" if x >= 0 else "negative")
    return (x - 2.0) ** 2 + abs(y - 1)


def main() -> None:
    study = optuna.create_study(
        direction="minimize",
        sampler=optuna.samplers.RandomSampler(seed=7),
    )
    study.set_user_attr("purpose", "optimization-workflows-smoke")

    seen_trials: list[int] = []

    def callback(study: optuna.study.Study, trial: optuna.trial.FrozenTrial) -> None:
        seen_trials.append(trial.number)
        if len(seen_trials) >= 8:
            study.stop()

    study.optimize(objective, n_trials=20, callbacks=[callback])

    assert len(study.trials) == 8
    assert seen_trials == list(range(8))
    assert study.user_attrs["purpose"] == "optimization-workflows-smoke"
    assert study.best_trial.state == optuna.trial.TrialState.COMPLETE
    assert set(study.best_params) == {"x", "y"}
    assert isinstance(study.best_value, float)
    assert all("branch" in trial.user_attrs for trial in study.trials)

    replayed_x = study.best_trial.suggest_float("x", -10.0, 10.0)
    assert replayed_x == study.best_params["x"]

    print(
        "basic optimization smoke passed: "
        f"trials={len(study.trials)} best_value={study.best_value:.6f} "
        f"best_params={study.best_params}"
    )


if __name__ == "__main__":
    main()
