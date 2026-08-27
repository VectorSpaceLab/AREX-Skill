#!/usr/bin/env python3
"""Deterministic Optuna ask-and-tell smoke test.

Adapted from Optuna's ask-and-tell tutorial into safe standalone checks for fixed
distributions, trial-number telling, and multi-objective value arity errors.
"""

from __future__ import annotations

import warnings

import optuna


def main() -> None:
    distributions = {
        "x": optuna.distributions.FloatDistribution(-3.0, 3.0),
        "degree": optuna.distributions.IntDistribution(1, 3),
        "shape": optuna.distributions.CategoricalDistribution(["linear", "quadratic"]),
    }

    study = optuna.create_study(
        direction="minimize",
        sampler=optuna.samplers.RandomSampler(seed=11),
    )

    pending: list[tuple[int, float, int, str]] = []
    for _ in range(6):
        trial = study.ask(distributions)
        assert set(trial.params) == set(distributions)
        pending.append(
            (
                trial.number,
                float(trial.params["x"]),
                int(trial.params["degree"]),
                str(trial.params["shape"]),
            )
        )

    for trial_number, x, degree, shape in pending:
        penalty = 0.0 if shape == "linear" else 0.25
        value = (x - 1.0) ** 2 + 0.1 * degree + penalty
        frozen = study.tell(trial_number, value)
        assert frozen.number == trial_number
        assert frozen.state == optuna.trial.TrialState.COMPLETE

    assert len(study.trials) == 6
    assert all(trial.value is not None for trial in study.trials)
    assert study.best_trial.params == study.best_params

    multi = optuna.create_study(directions=["minimize", "maximize"])
    bad_trial = multi.ask({"width": optuna.distributions.IntDistribution(1, 4)})
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        failed = multi.tell(bad_trial, 1.0)
    assert failed.state == optuna.trial.TrialState.FAIL
    assert failed.values is None
    assert any(
        "did not match the number of the objectives" in str(item.message)
        for item in caught
    )

    multi_trial = multi.ask({"width": optuna.distributions.IntDistribution(1, 4)})
    width = int(multi_trial.params["width"])
    recovered = multi.tell(multi_trial, [float(width), 1.0 / width])
    assert recovered.values == [float(width), 1.0 / width]
    assert len(multi.best_trials) == 1

    print(
        "ask-and-tell smoke passed: "
        f"single_trials={len(study.trials)} best_value={study.best_value:.6f} "
        f"multi_values={multi.best_trials[0].values}"
    )


if __name__ == "__main__":
    main()
