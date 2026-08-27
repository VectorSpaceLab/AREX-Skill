# Data streams

River streams are iterators of samples, not batch tensors. The core shape is one of the following:

- `(x, y)` for a normal supervised sample
- `(x, y, kwargs)` when extra per-sample arguments must be forwarded to `learn_one`
- `(x, None)` when only features are available
- `(x, y_dict)` when the target has multiple outputs

`x` is always a dictionary-like feature map in River-facing code. Feature names are hashable keys. Values may be mixed types as long as the downstream model can handle them.

## Dataset slices

Built-in datasets are iterable objects. Most file-backed datasets also expose a `path` property.

`Dataset.take(k)` returns the first `k` samples as an iterator. Use it when you need a bounded sample from a large, remote, or synthetic stream.

```python
from river import datasets

for x, y in datasets.Phishing().take(5):
    print(x, y)
```

## CSV streams

`stream.iter_csv` reads rows from a file path or text buffer.

Use it when CSV headers already identify feature names and you want the stream to stay dictionary-based.

Important behavior:

- Every field is a string by default.
- `target` can be `None`, a single column name, or a list of names for multioutput targets.
- `converters` cast named fields before the target is removed.
- `parse_dates` parses named fields with `datetime.strptime`.
- `drop` removes fields before conversion and target extraction.
- `drop_nones=True` removes fields whose converted value is `None`.
- `fraction < 1` samples rows deterministically when `seed` is set.
- `compression="infer"` handles compressed file paths.

```python
from river import stream

rows = stream.iter_csv(
    "data.csv",
    target="label",
    converters={"f1": float, "f2": int, "label": int},
    parse_dates={"moment": "%Y-%m-%dT%H:%M:%S"},
)
```

If the target name is wrong or missing, the target pop will fail with a key error.

## Array streams

`stream.iter_array` works with `numpy` arrays and also plain Python lists.

- 2D `X` becomes one feature dictionary per row.
- Feature names default to integer positions unless you provide `feature_names`.
- `y` may be `None`, a 1D target array, or a 2D multioutput target array.
- A 1D array of strings is treated as text-like data and yielded as raw strings.
- `shuffle=True` materializes the stream before permuting it.

```python
from river import stream

X = [[1, 2], [3, 4]]
y = [True, False]
rows = list(stream.iter_array(X, y, feature_names=["a", "b"]))
```

## Eager dataframe streams

`stream.iter_frame` is the preferred dataframe adapter.
It works with eager Narwhals-supported frames such as pandas, polars, PyArrow, Modin, and cuDF.

- Values keep their native per-column Python types.
- `y` may be a Series or a one-column / multi-column dataframe.
- `shuffle=True` materializes the rows first.
- Lazy frames are not supported.
- `stream.iter_pandas` and `stream.iter_polars` are deprecated wrappers that forward to `iter_frame`.

## LIBSVM and sparse text

`stream.iter_libsvm` reads sparse numeric samples in LIBSVM format.
Feature names are strings, feature values are floats, and the target is cast with `target_type`.

```python
from river import stream

dataset = stream.iter_libsvm("train.svm", target_type=int)
```

## SQL and scikit-learn sources

`stream.iter_sql` iterates over SQLAlchemy query results.
If `target_name` is provided, that column is popped from each row and returned as `y`.
If the connection supports result streaming, configure it on the connection to avoid eager prefetching.

`stream.iter_sklearn_dataset` converts a scikit-learn `Bunch` into a River stream.
It uses `iter_pandas` when the data payload is already a pandas dataframe and falls back to `iter_array` otherwise.

## Delayed-label streams

`stream.simulate_qa` turns a stream into a question-and-answer timeline.
It is the low-level helper behind delayed progressive validation.

- `moment` may be a feature name, a callable, or `None`.
- `delay` may be a feature name, a callable, a scalar, or a `datetime.timedelta`.
- The source stream must already be in arrival order. `simulate_qa` does not sort it for you.

The emitted shape is:

- `(i, x, None[, kwargs])` when the question is asked
- `(i, x, y[, kwargs])` when the answer arrives later

This shape is useful when you need to inspect the reveal order before calling evaluation utilities.
