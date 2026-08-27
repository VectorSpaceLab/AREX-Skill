---
name: optimization-workflows
description: "Core Optuna study and trial workflows: create/load/copy/delete
  studies, optimize objectives, run ask-and-tell loops, manage callbacks and
  attributes, handle fixed/reused parameters, and extract single- or
  multi-objective results."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Optuna Optimization Workflows

Use this sub-skill when the task is about the mechanics of running Optuna studies and trials: objective functions, `create_study`, `load_study`, `copy_study`, `delete_study`, `Study.optimize`, `Study.ask`, `Study.tell`, `Trial.suggest_*`, `Trial.report`, `Trial.should_prune`, callbacks, user attributes, fixed or reused parameters, and result extraction.

Route out of this sub-skill when the main problem is:
- Sampler or pruner algorithm selection/tuning: use `samplers-pruners`.
- Persistent storage URLs, CLI commands, or distributed workers: use `cli-and-storage`.
- Plotting, parameter importances, dashboards, or result analysis beyond basic extraction: use `analysis-visualization`.
- Artifact stores or third-party integrations: use `artifacts-integrations`.

## Fast Paths

- Start with `references/workflows.md` for copy-paste patterns covering normal optimization, ask-and-tell, callbacks, fixed parameters, and multi-objective studies.
- Use `references/api-reference.md` for exact signatures, result properties, and source-backed edge behavior.
- Use `references/troubleshooting.md` when Optuna raises direction/value mismatch, distribution compatibility, pruning/reporting, duplicate study, or callback errors.
- Run the bundled smoke checks from this directory:
  - `python scripts/basic_optimization_smoke.py`
  - `python scripts/ask_tell_smoke.py`

## Minimal Workflow

```python
import optuna


def objective(trial: optuna.Trial) -> float:
    x = trial.suggest_float("x", -10.0, 10.0)
    return (x - 2.0) ** 2


study = optuna.create_study(direction="minimize")
study.optimize(objective, n_trials=20)
print(study.best_value, study.best_params, study.best_trial.number)
```

## Key Rules

- Use `direction="minimize"` or `direction="maximize"` for single-objective studies; use `directions=[...]` only for multi-objective studies.
- `Study.optimize` expects an objective that returns one float for single-objective or one value per direction for multi-objective.
- `Study.ask()` returns a live `Trial`; finish it exactly once with `Study.tell(trial, value)` or `Study.tell(trial, state=optuna.trial.TrialState.PRUNED/FAIL)`.
- `Trial.report()` and `Trial.should_prune()` are for single-objective pruning workflows; multi-objective studies raise `NotImplementedError` for these methods.
- Use `study.best_trial`, `study.best_value`, and `study.best_params` for single-objective studies; use `study.best_trials` and each trial's `values` for multi-objective Pareto results.
- `study.best_trial` is a `FrozenTrial`; it can replay `suggest_*` calls with stored parameters, but `FrozenTrial.should_prune()` always returns `False`.
