# Generic Tuning Workflows

## Purpose

Use this reference for a complete KerasTuner search from a small model factory,
including conditional spaces, algorithm selection, result inspection, and
resume behavior. It complements the root workflow reference with tuning-route
specific decisions.

## Bounded model search

```python
import keras_tuner as kt
from tensorflow import keras


def build_model(hp):
    model = keras.Sequential([
        keras.layers.Input(shape=(3,)),
        keras.layers.Dense(
            hp.Choice("units", [4, 8]),
            activation=hp.Choice("activation", ["relu", "tanh"]),
        ),
        keras.layers.Dense(1, activation="sigmoid"),
    ])
    model.compile(optimizer="adam", loss="binary_crossentropy")
    return model


tuner = kt.RandomSearch(
    build_model,
    objective="val_loss",
    max_trials=2,
    directory="artifacts",
    project_name="small-search",
    overwrite=False,
)
tuner.search(x, y, validation_split=0.25, epochs=1, batch_size=4)
best_hp = tuner.get_best_hyperparameters(1)[0]
best_model = tuner.get_best_models(1)[0]
```

Use a small explicit `max_trials`, bounded epochs, and a writable project
folder while debugging. Expand the budget only after the model builds and
reports the intended objective.

## Conditional spaces

```python
def build_model(hp):
    family = hp.Choice("family", ["linear", "mlp"])
    if family == "linear":
        with hp.conditional_scope("family", "linear"):
            units = hp.Fixed("units", 1)
    else:
        with hp.conditional_scope("family", "mlp"):
            units = hp.Int("units", 4, 16, step=4)
    # Build a model using the active `units` value.
```

Only active conditional values belong in the current trial's `hp.values`.
Declare branch-specific parameters inside the matching scope and do not read a
branch-only value from a different branch.

## Algorithm decision

- Use `RandomSearch` for the first bounded smoke test.
- Use `GridSearch` only when every important dimension is finite; add `step`
  to numeric ranges when exhaustive coverage is required.
- Use `Hyperband` when the model training loop can honor the injected epoch and
  prior-trial parameters; set `factor >= 2` and keep `max_epochs` realistic.
- Use `BayesianOptimization` after installing SciPy and scikit-learn; choose
  it for expensive evaluations and a manageable-dimensional search space.

## Save and resume

The tuner stores state under `directory/project_name`. To resume a compatible
project, construct the tuner with the same directory/project name and
`overwrite=False`, then call `reload()` when needed:

```python
tuner.save()
# Later, in the same compatible environment:
tuner.reload()
print(tuner.remaining_trials)
```

Inspect `search_space_summary()` before searching and `results_summary()`
after searching. `get_best_hyperparameters()` returns configurations; use
the returned object to rebuild or retrain a final model on the full intended
dataset rather than assuming the checkpoint is a deployment refit.

## Custom black-box tuning

Subclass `Tuner` when the objective is not a normal Keras fit. Implement
`run_trial()` and return a float or metric dictionary. Implement
`save_model()`/`load_model()` if `get_best_models()` must work. Use
`FailedTrialError` for a trial-specific invalid configuration and `FatalError`
when the whole search must stop.
