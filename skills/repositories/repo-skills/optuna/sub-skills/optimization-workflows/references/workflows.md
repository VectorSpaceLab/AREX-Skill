# Optuna Optimization Workflow Recipes

These recipes are self-contained and avoid optional packages beyond Optuna's base dependencies.

## Basic Deterministic Optimization

```python
import optuna


def objective(trial: optuna.Trial) -> float:
    x = trial.suggest_float("x", -4.0, 4.0)
    y = trial.suggest_int("y", -2, 2)
    return (x - 1.5) ** 2 + abs(y - 1)


study = optuna.create_study(
    direction="minimize",
    sampler=optuna.samplers.RandomSampler(seed=0),
)
study.optimize(objective, n_trials=16)

assert len(study.trials) == 16
assert isinstance(study.best_value, float)
print(study.best_params)
```

Use a seeded sampler when examples, tests, or tutorials need stable behavior. Detailed sampler selection belongs in `samplers-pruners`.

## Continue an Existing Study

```python
study = optuna.create_study(direction="minimize")
study.optimize(objective, n_trials=5)
study.optimize(objective, n_trials=5)
assert len(study.trials) == 10
```

With persistent storage, name the study and use `load_if_exists=True` or `load_study`:

```python
study = optuna.create_study(
    study_name="demo",
    storage="sqlite:///demo.db",
    direction="minimize",
    load_if_exists=True,
)
```

Storage URL design, CLI storage commands, and parallel worker setup belong in `cli-and-storage`.

## Ask-and-Tell Equivalent of an Objective

Normal `optimize` style:

```python
def objective(trial: optuna.Trial) -> float:
    x = trial.suggest_float("x", -5.0, 5.0)
    return (x - 2.0) ** 2

study = optuna.create_study(direction="minimize")
study.optimize(objective, n_trials=8)
```

Ask-and-tell style:

```python
study = optuna.create_study(direction="minimize")
for _ in range(8):
    trial = study.ask()
    x = trial.suggest_float("x", -5.0, 5.0)
    value = (x - 2.0) ** 2
    study.tell(trial, value)
```

This is useful when evaluation already exists in another loop, when candidates are evaluated in batches, or when the objective needs state that is awkward to close over.

## Define-and-Run with Fixed Distributions

```python
distributions = {
    "x": optuna.distributions.FloatDistribution(-3.0, 3.0),
    "degree": optuna.distributions.IntDistribution(1, 3),
    "shape": optuna.distributions.CategoricalDistribution(["linear", "quadratic"]),
}

study = optuna.create_study(direction="minimize")
for _ in range(6):
    trial = study.ask(distributions)
    x = trial.params["x"]
    degree = trial.params["degree"]
    penalty = 0.0 if trial.params["shape"] == "linear" else 0.25
    study.tell(trial, (x - 1.0) ** 2 + 0.1 * degree + penalty)
```

When using fixed distributions, read sampled values from `trial.params` or call compatible `suggest_*` methods. Do not change a parameter name's distribution incompatibly across trials.

## Batched Ask-and-Tell

```python
study = optuna.create_study(direction="minimize")
for _ in range(3):
    pending = []
    for _ in range(4):
        trial = study.ask()
        x = trial.suggest_float("x", -2.0, 2.0)
        pending.append((trial.number, x))

    for trial_number, x in pending:
        study.tell(trial_number, x**2)
```

Keep either the `Trial` object or `trial.number` for every pending candidate. For high-concurrency sampler behavior, route to `samplers-pruners`.

## Objective Pruning Pattern

```python
import optuna


def objective(trial: optuna.Trial) -> float:
    best_loss = float("inf")
    for step in range(5):
        lr = trial.suggest_float("lr", 1e-3, 1.0, log=True)
        loss = (lr - 0.1) ** 2 + 1.0 / (step + 1)
        best_loss = min(best_loss, loss)
        trial.report(best_loss, step)
        if trial.should_prune():
            raise optuna.TrialPruned()
    return best_loss
```

`report` and `should_prune` are single-objective only. Choosing and tuning pruners belongs in `samplers-pruners`.

## Ask-and-Tell Pruning State

```python
study = optuna.create_study(direction="minimize")
trial = study.ask()
for step in range(3):
    trial.report(10.0 - step, step)
    if trial.should_prune():
        study.tell(trial, state=optuna.trial.TrialState.PRUNED)
        break
else:
    study.tell(trial, 7.0)
```

When telling a pruned trial, pass `state=TrialState.PRUNED` rather than a completed objective value.

## Callbacks and Early Stop

Callbacks passed to `Study.optimize` receive `(study, frozen_trial)` after each trial finishes. Use them for logging, custom stop criteria, or side effects that should observe completed trials.

```python
class StopAfterGoodValue:
    def __init__(self, threshold: float) -> None:
        self.threshold = threshold

    def __call__(self, study: optuna.study.Study, trial: optuna.trial.FrozenTrial) -> None:
        if trial.value is not None and trial.value <= self.threshold:
            study.stop()


study = optuna.create_study(direction="minimize")
study.optimize(objective, n_trials=100, callbacks=[StopAfterGoodValue(0.01)])
```

Call `study.stop()` only inside an active `optimize` callback or objective path. Calling it outside optimization raises `RuntimeError`.

## Fixed Starting Points and Imported Results

Ask Optuna to evaluate known parameter sets:

```python
study = optuna.create_study(direction="minimize")
study.enqueue_trial({"x": 0.0, "y": 1})
study.optimize(objective, n_trials=3)
```

Register an already evaluated result:

```python
trial = optuna.trial.create_trial(
    params={"x": 0.0},
    distributions={"x": optuna.distributions.FloatDistribution(-1.0, 1.0)},
    value=1.0,
)
study.add_trial(trial)
```

For multi-objective imported results, use `values=[...]` whose length matches `directions`.

## Reusing the Best Trial

```python
def detailed_eval(trial: optuna.trial.FrozenTrial) -> dict[str, float]:
    x = trial.suggest_float("x", -4.0, 4.0)
    return {"loss": (x - 1.5) ** 2, "absolute_error": abs(x - 1.5)}

metrics = detailed_eval(study.best_trial)
```

This replays stored parameters. It does not create a new trial and does not support meaningful pruning.

## Multi-Objective Basics

```python
import optuna


def objective(trial: optuna.Trial) -> tuple[float, float]:
    x = trial.suggest_float("x", -2.0, 2.0)
    model_size = trial.suggest_int("model_size", 1, 5)
    loss = (x - 0.5) ** 2 + 0.1 * model_size
    speed = 1.0 / model_size
    return loss, speed


study = optuna.create_study(directions=["minimize", "maximize"])
study.optimize(objective, n_trials=12)
pareto_trials = study.best_trials
for trial in pareto_trials:
    print(trial.number, trial.values, trial.params)
```

Rules:
- The objective must return exactly one value per direction.
- Use `study.best_trials`, not `study.best_trial`, for Pareto-front results.
- Avoid `Trial.report` and `Trial.should_prune` in multi-objective objectives.
- Visualization of the Pareto front belongs in `analysis-visualization`.

## Study Attributes

```python
study = optuna.create_study(direction="minimize")
study.set_user_attr("dataset", "synthetic")


def objective(trial: optuna.Trial) -> float:
    trial.set_user_attr("phase", "warmup" if trial.number < 3 else "main")
    x = trial.suggest_float("x", -1.0, 1.0)
    return x**2
```

Use user attributes for reproducible metadata that should travel with study/trial records. Avoid relying on private system attributes in public examples.

## Copy and Delete Studies

```python
optuna.copy_study(
    from_study_name="source",
    from_storage="sqlite:///source.db",
    to_storage="sqlite:///archive.db",
    to_study_name="source-copy",
)
optuna.delete_study(study_name="source-copy", storage="sqlite:///archive.db")
```

A copied study preserves directions, user attributes, system attributes, and trials. Copying to an existing destination study name raises a duplicate-study error unless you choose a different `to_study_name`.
