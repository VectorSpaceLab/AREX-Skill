# Tuner Reference

## String tuner names

`ak.AutoModel(..., tuner="...")` accepts exactly these strings:

| String | Class |
| --- | --- |
| `"greedy"` | `ak.Greedy` |
| `"random"` | `ak.RandomSearch` |
| `"hyperband"` | `ak.Hyperband` |
| `"bayesian"` | `ak.BayesianOptimization` |

Any other string raises a `ValueError` saying the tuner argument must be one of those names.

## Verified tuner signatures

```python
ak.Greedy(hypermodel, objective="val_loss", max_trials=10, initial_hps=None, seed=None, hyperparameters=None, tune_new_entries=True, allow_new_entries=True, **kwargs)
ak.RandomSearch(hypermodel=None, objective=None, max_trials=10, seed=None, hyperparameters=None, tune_new_entries=True, allow_new_entries=True, max_retries_per_trial=0, max_consecutive_failed_trials=3, **kwargs)
ak.Hyperband(max_epochs=1000, max_trials=100, *args, **kwargs)
ak.BayesianOptimization(hypermodel=None, objective=None, max_trials=10, num_initial_points=None, alpha=0.0001, beta=2.6, seed=None, hyperparameters=None, tune_new_entries=True, allow_new_entries=True, max_retries_per_trial=0, max_consecutive_failed_trials=3, **kwargs)
```

## Task-specific defaults

When `tuner=None`, source code sets these defaults:

| Task class | Default tuner behavior |
| --- | --- |
| `ImageClassifier` | task-specific `Greedy` tuner with image classifier initial hyperparameters |
| `TextClassifier` | task-specific `Greedy` tuner with text classifier initial hyperparameters |
| `StructuredDataClassifier` | task-specific `Greedy` tuner with structured-data classifier initial hyperparameters |
| `StructuredDataRegressor` | task-specific `Greedy` tuner with structured-data regressor initial hyperparameters |
| `ImageRegressor` | `Greedy` |
| `TextRegressor` | `Greedy` |
| `AutoModel` | string default `"greedy"` |
