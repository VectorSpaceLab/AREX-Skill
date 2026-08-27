# Task API Troubleshooting

## Backend import fails

Set `KERAS_BACKEND` before Python imports Keras or AutoKeras, install AutoKeras in the active Python environment, and verify the backend framework import. Use the root `scripts/check_autokeras_env.py` helper.

## Structured-data `column_types` value error

Symptom:

```text
column_types should be either "categorical" or "numerical"
```

Use exactly `"categorical"` or `"numerical"`; avoid aliases such as `"numeric"` or dtype objects.

## Structured-data column name mismatch

Symptom:

```text
column_names and column_types are mismatched. Cannot find column name ... in the data.
```

Make `column_names` exactly match the feature columns passed as `x`, remove target columns from features, and ensure every `column_types` key appears in `column_names`.

## Non-NumPy or wrong number of arrays

Task classes are single-input/single-output wrappers. For multiple inputs or multiple outputs, use `../automodel-customization/SKILL.md`. Convert DataFrames to arrays when direct adapter behavior is not intended.

## Missing validation data or split

Pass either `validation_split=0.2` or `validation_data=(x_val, y_val)`. For tiny datasets, explicit validation data can be safer than a split.

## Original tutorial downloads are slow or blocked

Use synthetic workflows or bundled scripts instead of dataset-backed examples. Only run external dataset examples when network, storage, and runtime budget are explicitly available.

## Search takes too long

Default `max_trials=100` is a real AutoML search. Start with:

```python
model = ak.ImageClassifier(max_trials=1, overwrite=True)
model.fit(x, y, epochs=1, batch_size=2, validation_split=0.25)
```

For search control and persistence, use `../search-and-export/SKILL.md`.
