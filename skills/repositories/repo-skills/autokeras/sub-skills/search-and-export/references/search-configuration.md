# Search Configuration

## Common constructor controls

- `max_trials`: maximum candidate Keras models to evaluate. Default `100` is a real search; use `1` for smoke checks.
- `tuner`: a string or tuner class. Strings accepted by `AutoModel` are `"greedy"`, `"random"`, `"hyperband"`, and `"bayesian"`.
- `objective`: objective name such as `"val_loss"` or `"val_accuracy"`. It must match a metric/loss produced during validation.
- `directory`: directory used by KerasTuner/AutoKeras to store search artifacts.
- `project_name`: subdirectory/name for the search project; defaults vary by task class.
- `overwrite`: `False` reloads an existing project when present; `True` starts fresh in that project directory.
- `seed`: sets random seed for reproducible search sampling where supported.
- `max_model_size`: rejects candidate models with too many scalar parameters.

## Smoke search settings

```python
model = ak.ImageClassifier(max_trials=1, overwrite=True, directory="ak_smoke", project_name="image_classifier_smoke", seed=5)
model.fit(x, y, epochs=1, validation_split=0.25, batch_size=2)
```

Use a temporary or disposable `directory` for smoke checks so old search state cannot affect the result.

## Validation behavior

`AutoModel.fit` requires a validation source. If `validation_data` is supplied, AutoKeras sets `validation_split` to zero internally. If neither validation source is provided, AutoKeras raises an error.

## Epochs and callbacks

- If `epochs` is `None`, AutoKeras can use a large internal maximum with `EarlyStopping` to find a suitable epoch count.
- If callbacks do not include `keras.callbacks.EarlyStopping`, AutoKeras may insert early stopping for search acceleration.
- For deterministic bounded smoke checks, pass `epochs=1`.
- In non-interactive logs, `verbose=2` is often easier to read than progress bars.

## Persistence checklist

Before changing a search, check whether `directory/project_name` points at an old project, whether this run should resume or start fresh, whether input columns/target/objective changed, and whether `overwrite=True` is safe for this scratch project.
