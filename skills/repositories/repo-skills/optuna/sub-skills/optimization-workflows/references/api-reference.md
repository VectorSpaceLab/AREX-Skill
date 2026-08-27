# Optimization Workflow API Reference

This reference covers core Optuna study/trial APIs verified for Optuna package `optuna` version `5.0.0.dev0`.

## Study Lifecycle

```python
optuna.create_study(
    *, storage=None, sampler=None, pruner=None, study_name=None,
    direction=None, load_if_exists=False, directions=None
) -> optuna.study.Study

optuna.load_study(*, study_name, storage, sampler=None, pruner=None) -> optuna.study.Study
optuna.copy_study(*, from_study_name, from_storage, to_storage, to_study_name=None) -> None
optuna.delete_study(*, study_name, storage) -> None
```

Use `create_study` for new studies. With persistent storage, pass `study_name` and `load_if_exists=True` to resume an existing named study without raising a duplicate-study error. Use `load_study` for an existing persistent study; in-memory studies are not normally loaded by name across processes.

Direction rules:
- Single objective: `direction="minimize"` or `direction="maximize"`.
- Multi-objective: `directions=["minimize", "maximize", ...]` with one entry per returned objective value.
- Do not pass a list to `direction`; do not pass a string to `directions`.
- Default single-objective direction is minimize.

Default algorithm behavior is sampler/pruner territory, but workflow authors should know that single-objective studies use a single-objective sampler by default and multi-objective studies use a multi-objective-capable default sampler.

## Running Objectives

```python
Study.optimize(
    func, n_trials=None, timeout=None, n_jobs=1, catch=(), callbacks=None,
    gc_after_trial=False, show_progress_bar=False
) -> None
```

The objective receives an active `optuna.Trial` and returns objective value(s):

```python
def objective(trial: optuna.Trial) -> float:
    width = trial.suggest_int("width", 1, 5)
    scale = trial.suggest_float("scale", 1e-3, 1.0, log=True)
    return (width - 3) ** 2 + scale
```

Important behavior:
- Re-calling `study.optimize(objective, n_trials=...)` continues the same study and appends trials.
- If the objective raises an exception not listed in `catch`, optimization stops after recording a failed trial and re-raises the exception.
- If the exception type is in `catch`, optimization continues and failed trials remain in the history.
- `n_jobs` can run trials concurrently, but objective code must be thread/process safe for the selected storage and workload.
- Nested `study.optimize(...)` from inside an objective is invalid and raises `RuntimeError`.

## Trial Suggestions

Common active-trial methods:

```python
Trial.suggest_float(name, low, high, *, step=None, log=False) -> float
Trial.suggest_int(name, low, high, *, step=1, log=False) -> int
Trial.suggest_categorical(name, choices) -> value
```

Search-space rules:
- Reusing the same parameter name inside a trial returns the same value if the distribution is compatible.
- Reusing a parameter name with an incompatible distribution raises `ValueError`.
- `suggest_float(..., log=True)` cannot be combined with `step`.
- `suggest_int(..., log=True)` requires `step=1`.
- Numeric distribution bounds must form a non-empty range and step values must be positive.
- Categorical choices for an existing parameter name cannot be changed dynamically in an incompatible way.

## Pruning Hooks

```python
Trial.report(value, step) -> None
Trial.should_prune() -> bool
```

Use these only in single-objective studies. `Trial.report` records an intermediate float value for a non-negative integer step. `Trial.should_prune` asks the study's pruner whether to stop the current trial. Raise `optuna.TrialPruned` in an objective, or use `Study.tell(..., state=TrialState.PRUNED)` in ask-and-tell.

Report/Prune edge behavior:
- `value` must be castable to `float`; invalid values raise `TypeError`.
- `step` must be castable to `int` and non-negative; invalid types raise `TypeError`, negative steps raise `ValueError`.
- Reporting twice at the same step warns and keeps the first report.
- Multi-objective studies raise `NotImplementedError` for both `report` and `should_prune`.

## Ask-and-Tell

```python
Study.ask(fixed_distributions=None) -> optuna.Trial
Study.tell(trial, values=None, state=None, skip_if_finished=False) -> optuna.trial.FrozenTrial
```

Use ask-and-tell when the evaluation loop lives outside a normal objective function, when batching candidates, or when using define-and-run fixed distributions.

```python
study = optuna.create_study(direction="minimize")
trial = study.ask()
x = trial.suggest_float("x", -5.0, 5.0)
value = (x - 1.0) ** 2
frozen = study.tell(trial, value)
```

Notes:
- `trial` can be the active `Trial` object or its integer trial number.
- For single-objective completion, pass one float as `values`.
- For multi-objective completion, pass a sequence whose length equals `len(study.directions)`.
- For pruned or failed trials, pass `state=optuna.trial.TrialState.PRUNED` or `FAIL`; omit completed values for states that should not have objective values.
- `skip_if_finished=True` avoids raising if the trial was already finished.

Define-and-run fixed distributions:

```python
distributions = {
    "x": optuna.distributions.FloatDistribution(-5.0, 5.0),
    "model": optuna.distributions.CategoricalDistribution(["small", "large"]),
}
trial = study.ask(distributions)
value = trial.params["x"] ** 2
study.tell(trial, value)
```

## Manual and Reused Trials

```python
Study.enqueue_trial(params, user_attrs=None, skip_if_exists=False) -> None
Study.add_trial(trial) -> None
optuna.trial.create_trial(..., value=None, values=None, params=None, distributions=None, ...) -> FrozenTrial
```

Use `enqueue_trial` to ask Optuna to evaluate specified parameters in future trials. Use `add_trial` with `create_trial` to register already-evaluated completed, pruned, or failed trials. When adding completed trials, `value`/`values`, `params`, and matching `distributions` must be consistent with the study's objective count.

## Attributes and Result Extraction

Study-level metadata:

```python
study.set_user_attr("dataset", "synthetic-v1")
study.user_attrs
```

Trial-level metadata:

```python
def objective(trial):
    trial.set_user_attr("fold", 0)
    ...
```

Single-objective result properties:
- `study.best_value`: best scalar objective value.
- `study.best_params`: best trial's parameter dictionary.
- `study.best_trial`: best `FrozenTrial`.
- `study.trials`: all `FrozenTrial` records.

Multi-objective result properties:
- `study.directions`: objective directions.
- `study.best_trials`: Pareto-front `FrozenTrial` records.
- `trial.values`: objective sequence for each completed multi-objective trial.

## FrozenTrial Reuse

`study.best_trial` and entries in `study.best_trials` are `FrozenTrial` objects. They can replay the same `suggest_*` calls to return stored parameters, which is useful for post-optimization evaluation:

```python
best = study.best_trial
x = best.suggest_float("x", -10.0, 10.0)
```

Do not expect pruning to work on frozen trials; `FrozenTrial.should_prune()` always returns `False`.
