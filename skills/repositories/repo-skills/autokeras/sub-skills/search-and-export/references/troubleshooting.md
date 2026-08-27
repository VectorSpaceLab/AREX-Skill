# Search and Export Troubleshooting

## Invalid tuner name

Use one of `"greedy"`, `"random"`, `"hyperband"`, or `"bayesian"`, or pass a class such as `ak.RandomSearch`.

## Missing validation data or split

Pass either `validation_split=0.2` or `validation_data=(x_val, y_val)`. For very small datasets, explicit validation data can avoid class imbalance from a split.

## Stale search project is reused

`overwrite=False` reuses an existing `directory/project_name` project. Use `overwrite=True` for disposable fresh runs or change `project_name` when data schema, target type, objective, or graph topology changes.

## Objective or metric mismatch

Use `objective="val_loss"` as a general default. For classifiers with accuracy metrics, use `"val_accuracy"` only when the model reports accuracy under that name. For multiple outputs, inspect Keras metric names before choosing a custom objective.

## Search is unexpectedly slow

Default `max_trials=100` and `epochs=None` can be expensive. Start with `max_trials=1`, `epochs=1`, small data, and `batch_size=2`.

## Exported model fails to load

Retry with:

```python
from keras.models import load_model
import autokeras as ak
loaded = load_model("model_autokeras.keras", custom_objects=ak.CUSTOM_OBJECTS)
```

Also ensure compatible Keras and AutoKeras versions in the target environment.
