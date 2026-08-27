# Task API Reference

## Purpose

Use this reference to choose and configure AutoKeras high-level supervised task classes. The signatures below are verified from AutoKeras 3.0.0 source and installed-package inspection.

## Shared workflow methods

All six task classes inherit the `AutoModel` workflow surface:

```python
history = model.fit(x, y, epochs=1, validation_split=0.2, callbacks=None, **keras_fit_kwargs)
predictions = model.predict(x_test, batch_size=32)
metrics = model.evaluate(x_test, y_test, batch_size=32)
keras_model = model.export_model()
```

Important shared constructor fields:

- `max_trials`: maximum candidate Keras models to try. Use `1` for smoke checks; larger values are real searches.
- `directory` and `project_name`: where KerasTuner search state is stored. Use a task-specific scratch directory for experiments.
- `overwrite`: `False` can resume an existing project with the same directory/name; use `True` for a fresh disposable run.
- `objective`: metric/loss name optimized by the tuner. Make sure it is produced by the model metrics/losses.
- `tuner`: a tuner string or tuner class. See `../search-and-export/SKILL.md` for details.
- `seed`: repeatable initialization/search sampling where supported.
- `max_model_size`: reject candidate models larger than this parameter-count limit.

`fit` requires either `validation_data` or a non-zero `validation_split`. If both are omitted or `validation_split=0` without `validation_data`, AutoKeras raises an error. When `validation_data` is supplied, it overrides `validation_split`.

## Image tasks

### `ak.ImageClassifier`

```python
ak.ImageClassifier(num_classes=None, multi_label=False, loss=None, metrics=None,
                   project_name="image_classifier", max_trials=100,
                   directory=None, objective="val_loss", tuner=None,
                   overwrite=False, seed=None, max_model_size=None, **kwargs)
```

Use for image classification. `x` should be a NumPy array shaped `(samples, width, height)` or `(samples, width, height, channels)`. Labels may be raw class labels, binary labels, one-hot labels, or multi-label binary matrices when `multi_label=True`. When `num_classes` is `None`, AutoKeras infers it from training data.

### `ak.ImageRegressor`

```python
ak.ImageRegressor(output_dim=None, loss="mean_squared_error", metrics=None,
                  project_name="image_regressor", max_trials=100,
                  directory=None, objective="val_loss", tuner=None,
                  overwrite=False, seed=None, max_model_size=None, **kwargs)
```

Use for numeric targets from image arrays. `output_dim=None` infers target dimensionality from `y`.

## Text tasks

### `ak.TextClassifier`

```python
ak.TextClassifier(num_classes=None, multi_label=False, loss=None, metrics=None,
                  project_name="text_classifier", max_trials=100,
                  directory=None, objective="val_loss", tuner=None,
                  overwrite=False, seed=None, max_model_size=None, **kwargs)
```

Use for classification over 1D arrays of full-sentence strings. AutoKeras casts to string and tokenizes internally through text hyper-preprocessors.

### `ak.TextRegressor`

```python
ak.TextRegressor(output_dim=None, loss="mean_squared_error", metrics=None,
                 project_name="text_regressor", max_trials=100,
                 directory=None, objective="val_loss", tuner=None,
                 overwrite=False, seed=None, max_model_size=None, **kwargs)
```

Use for numeric targets from 1D text string arrays.

## Structured-data tasks

### `ak.StructuredDataClassifier`

```python
ak.StructuredDataClassifier(column_names=None, column_types=None,
                            num_classes=None, multi_label=False, loss=None,
                            metrics=None, project_name="structured_data_classifier",
                            max_trials=100, directory=None,
                            objective="val_accuracy", tuner=None,
                            overwrite=False, seed=None, max_model_size=None,
                            **kwargs)
```

Use for tabular classification. `x` may be a 2D NumPy array, a pandas-like table converted to arrays, or a CSV-path style input supported by AutoKeras' adapters. `column_names` names every feature column; `column_types` maps a subset or all column names to either `"categorical"` or `"numerical"`. If `column_types` names a column that is absent from `column_names`, `fit` raises a mismatch error.

### `ak.StructuredDataRegressor`

```python
ak.StructuredDataRegressor(column_names=None, column_types=None, output_dim=None,
                           loss="mean_squared_error", metrics=None,
                           project_name="structured_data_regressor",
                           max_trials=100, directory=None,
                           objective="val_loss", tuner=None, overwrite=False,
                           seed=None, max_model_size=None, **kwargs)
```

Use for numeric targets from tabular data. `column_names` and `column_types` behave as in the classifier.

## Method output expectations

- `fit` returns a Keras `History` object for the best model's final training path when training completes.
- `predict` returns a NumPy array for single-output tasks; output shape follows the target head.
- `evaluate` returns Keras evaluation values for the best model.
- `export_model` returns the best searched `keras.Model`. Use the search/export sub-skill for save/reload details.

## Defaults that often surprise users

- Default `max_trials=100` is a real search, not a quick demo.
- If `epochs=None`, AutoKeras can use adaptive early-stopping behavior rather than a fixed tiny training run.
- `StructuredDataClassifier` defaults to `objective="val_accuracy"`; most other high-level classes default to `"val_loss"`.
- Task-specific classifiers often use task-specific default tuners when `tuner=None`; details are in `../search-and-export/references/tuner-reference.md`.
