# Workflows

## Purpose

Read this when you need end-to-end tuning patterns rather than individual signatures. The examples below are intentionally small and use synthetic data so they are easy to adapt.

## 1) Generic Keras model search

The common pattern is:

1. Write `build_model(hp)` and use `hp.Choice`, `hp.Int`, `hp.Float`, `hp.Boolean`, or `hp.Fixed` to define the search space.
2. Instantiate one of the built-in tuners, usually `RandomSearch`, `GridSearch`, `Hyperband`, or `BayesianOptimization`.
3. Call `search(...)` with your training data and validation data.
4. Inspect the top trials with `get_best_models()` or `get_best_hyperparameters()`.
5. Use `save()` / `reload()` to resume a stopped project.

Example:

```python
import keras_tuner as kt
from tensorflow import keras


def build_model(hp):
    model = keras.Sequential([
        keras.layers.Input(shape=(3,)),
        keras.layers.Dense(hp.Choice("units", [4, 8]), activation="relu"),
        keras.layers.Dense(1, activation="sigmoid"),
    ])
    model.compile(optimizer="adam", loss="binary_crossentropy")
    return model


tuner = kt.RandomSearch(
    build_model,
    objective="val_loss",
    max_trials=2,
    directory="/path/to/kt-runs",  # replace with <KT_RUN_DIR>
    project_name="demo",
)
tuner.search(x_train, y_train, validation_split=0.2, epochs=1)
best_model = tuner.get_best_models()[0]
```

## 2) Search-space design

Use `conditional_scope` when one hyperparameter only exists under a parent choice.
This keeps inactive values out of `hp.values` and makes grid/bayesian search behave predictably.

Typical patterns:

- `hp.Choice("model_type", ["mlp", "cnn"])` to branch on architecture family.
- `with hp.conditional_scope("model_type", ["cnn"]): ...` to register CNN-only parameters.
- `hp.Int("layers", 1, 4)` for small integer ranges.
- `hp.Float("dropout", 0.0, 0.6, step=0.1)` for bounded floating-point grids.
- `hp.Fixed("loss", "binary_crossentropy")` when a value must appear in the search state but should not be tuned.

`GridSearch` only exhausts finite spaces. If you leave `step` unspecified for a `Float` or use a log-sampled `Int` without a `step`, KerasTuner samples 10 values for that dimension.

## 3) Resume and inspect an existing search

`save()` and `reload()` are useful when a project is interrupted:

```python
tuner.save()
# ... later ...
tuner.reload()
```

After the search, use:

```python
best_hps = tuner.get_best_hyperparameters()[0]
best_model = tuner.get_best_models()[0]
tuner.search_space_summary()
tuner.results_summary()
```

## 4) Custom `Tuner` or black-box objective

Subclass `Tuner` when you want to tune something that is not a standard Keras model or when you need a custom training loop.

Implement at least:

- `run_trial(self, trial, *args, **kwargs)`.
- `save_model(self, trial_id, model, step=0)` and `load_model(self, trial)` if you want best-model restoration.

A black-box search can return a float, a dict, a `History`, or a list of those values.

## 5) When to prefer each algorithm

- `RandomSearch`: simple baseline and quickest to explain.
- `GridSearch`: finite discrete spaces where full coverage matters.
- `Hyperband`: epoch-budgeted training where early stopping can save time.
- `BayesianOptimization`: smaller search spaces with expensive evaluations.

## 6) Notes that matter in practice

- `Hyperband` injects special `tuner/*` hyperparameters during later rounds.
- `BayesianOptimization` needs SciPy and scikit-learn.
- `results_summary()` prints the trials currently known to the oracle, so call it after `search()` or `reload()`.
- `get_best_models()` depends on the tuning directory being writable because trials are saved there.
