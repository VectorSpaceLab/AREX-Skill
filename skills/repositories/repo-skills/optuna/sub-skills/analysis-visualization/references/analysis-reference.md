# Analysis Reference

This reference covers post-optimization analysis for completed Optuna studies: parameter importances and trial dataframe export.

## Parameter Importances

Primary API:

```python
optuna.importance.get_param_importances(
    study,
    *,
    evaluator=None,
    params=None,
    target=None,
    normalize=True,
)
```

Return value: an ordered `dict[str, float]` where keys are parameter names and values are non-negative importance scores in descending order. With `normalize=True`, values sum to `1.0` unless there are no parameters.

Typical single-objective usage:

```python
import optuna
from optuna.importance import PedAnovaImportanceEvaluator, get_param_importances

study = optuna.create_study(direction="minimize")
study.optimize(lambda trial: (trial.suggest_float("lr", 1e-4, 1e-1, log=True) - 0.01) ** 2, n_trials=12)

importances = get_param_importances(
    study,
    evaluator=PedAnovaImportanceEvaluator(),
    params=["lr"],
)
```

Evaluator choices:

- `FanovaImportanceEvaluator`: default evaluator when `evaluator=None`; requires `scikit-learn`.
- `MeanDecreaseImpurityImportanceEvaluator`: random-forest based; requires `scikit-learn`.
- `PedAnovaImportanceEvaluator`: lightweight alternative useful for smoke checks and dashboard-like summaries.
- Custom evaluators must subclass `optuna.importance.BaseImportanceEvaluator` and implement compatible `evaluate(...)` behavior.

Important semantics:

- Completed trials only are used.
- If `params=None`, Optuna evaluates parameters present in all completed trials; conditional parameters can be excluded.
- If `params=[]`, Optuna returns `{}`.
- If `params=[...]`, only completed trials containing every named parameter are considered.
- Multi-objective studies require `target`, for example `target=lambda trial: trial.values[0]`.
- `normalize=False` is experimental and can emit an `ExperimentalWarning`.

Multi-objective target example:

```python
first_objective_importances = get_param_importances(
    study,
    evaluator=PedAnovaImportanceEvaluator(),
    params=["x", "y"],
    target=lambda trial: trial.values[0],
)
```

Duration or metadata target example:

```python
duration_importances = get_param_importances(
    study,
    evaluator=PedAnovaImportanceEvaluator(),
    target=lambda trial: trial.duration.total_seconds(),
)
```

## Trial Dataframe Export

Primary API:

```python
Study.trials_dataframe(
    attrs=(
        "number",
        "value",
        "datetime_start",
        "datetime_complete",
        "duration",
        "params",
        "user_attrs",
        "system_attrs",
        "state",
    ),
    multi_index=False,
)
```

Return value: a `pandas.DataFrame`. This requires `pandas` to be installed.

Common usage:

```python
df = study.trials_dataframe()
df.to_csv("trials.csv", index=False)
```

Select fewer columns:

```python
df = study.trials_dataframe(attrs=("number", "value", "params", "state"))
```

Use hierarchical columns:

```python
df = study.trials_dataframe(attrs=("number", "params", "user_attrs"), multi_index=True)
```

Column behavior:

- With `multi_index=False`, nested fields are flattened, for example `params_x`.
- With `multi_index=True`, nested fields use hierarchical columns such as `("params", "x")`.
- In multi-objective studies, requesting `"value"` is implicitly replaced by `"values"`.
- If metric names are set with `Study.set_metric_names(...)`, value columns use those objective names.
- Empty studies return an empty dataframe, not a failed optimization.

## Robust Analysis Workflow

1. Confirm the study has enough completed trials for the requested analysis.
2. Pick a deterministic evaluator when reproducibility matters.
3. Pass `params=[...]` for conditional parameters or strict feature subsets.
4. Pass `target=...` for multi-objective studies or non-objective quantities such as duration.
5. Treat `pandas` and `scikit-learn` as optional dependencies and catch `ImportError`/`ModuleNotFoundError` around dataframe and fANOVA-style analysis.

```python
from optuna.importance import PedAnovaImportanceEvaluator, get_param_importances

completed = [trial for trial in study.trials if trial.state.name == "COMPLETE"]
if len(completed) >= 2:
    importances = get_param_importances(
        study,
        evaluator=PedAnovaImportanceEvaluator(),
        params=["x", "y"],
        target=None,
    )
else:
    importances = {}
```
