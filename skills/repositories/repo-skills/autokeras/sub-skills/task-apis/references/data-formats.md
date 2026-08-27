# Data Formats for AutoKeras Task APIs

## Image arrays

Image task classes expect NumPy arrays:

```text
x shape for grayscale: (samples, width, height)
x shape for explicit channels: (samples, width, height, channels)
```

AutoKeras expands a grayscale image input's last dimension internally when needed. For quick checks, use small float32 arrays. Real images should be consistently sized before `fit`.

Classification labels can be raw integer labels, binary labels, one-hot arrays, or multi-label binary arrays. Regression targets should be numeric arrays, commonly `(samples,)` or `(samples, 1)`.

## Text arrays

Text task classes expect a one-dimensional array of strings:

```python
x = np.array(["a short sentence about cats", "a different sentence about dogs"])
```

Each element is treated as a full text example. Avoid pre-tokenized integer sequences unless intentionally building a custom `AutoModel` graph.

## Structured data

Structured-data task classes expect a 2D feature table. Useful forms include a NumPy array, a DataFrame converted to `.to_numpy()`, or a CSV-path workflow supported by AutoKeras adapters.

`column_names` should name every feature column in order. `column_types` maps column names to `"numerical"` or `"categorical"`:

```python
column_names = ["age", "fare", "ticket_class", "embark_town"]
column_types = {
    "age": "numerical",
    "fare": "numerical",
    "ticket_class": "categorical",
    "embark_town": "categorical",
}
```

Rules backed by source/tests:

- Every `column_types` value must be exactly `"categorical"` or `"numerical"`.
- If `column_types` is supplied, referenced names must appear in `column_names`.
- If `column_types` is omitted, AutoKeras infers types from the data. A column with a low unique-value ratio can be treated as categorical.
- Mixed string/numeric arrays are accepted by structured-data adapters, but keep columns consistent across train, validation, predict, and evaluate.

## Validation data

Use one of these forms:

```python
model.fit(x_train, y_train, validation_split=0.2, epochs=1)
model.fit(x_train, y_train, validation_data=(x_val, y_val), epochs=1)
```

`validation_data` overrides `validation_split`. If both validation sources are absent or disabled, AutoKeras raises an error requiring either validation data or a non-zero split.
