# Local Tensor and DataFrame Workflows

## Purpose

Read this for the shortest reliable path to a local Mars session, a tiny tensor
or DataFrame example, and the execution model around `execute()` and `fetch()`.

## 1) Start a local session

```python
import mars

session = mars.new_session()
```

Use a local session when you want repeatable behavior across several objects or
when a snippet should be explicit about where work executes. If you only need a
one-off object, Mars can still create a default session lazily.

Stop the session when you are done:

```python
mars.stop_server()
```

## 2) Run a tiny tensor example

```python
import mars.tensor as mt

x = mt.arange(6, chunk_size=3).reshape((2, 3))
result = x.sum().execute().fetch()
```

Use this pattern when the user wants a NumPy-like example, shape reasoning, or a
sanity check that the package is working on CPU.

## 3) Run a tiny DataFrame example

```python
import mars.dataframe as md

df = md.DataFrame({"a": [1, 2, 3], "b": [10, 20, 30]})
summary = df.sum().execute().fetch()
```

Use this pattern when the user wants pandas-like behavior, small grouping, or
columnwise aggregation.

## 4) Switch eager mode for debugging

```python
from mars.config import option_context
import mars.tensor as mt

with option_context({"eager_mode": True}):
    x = mt.arange(3)
    y = x.sum()
```

Eager mode is helpful when a user expects immediate values while debugging.
Use it briefly, not as a default for large computations.

## 5) Tiny file-backed IO

- Use a temporary local CSV, HDF5, or Parquet file.
- Keep the fixture tiny.
- Prefer documented local paths over remote storage or credentialed services.

Example shapes to keep in mind:

```python
md.read_csv("tmp.csv")
mt.from_hdf5("tmp.hdf5", dataset="t")
mt.to_hdf5("out.hdf5", mt.ones((3, 3)), dataset="r").execute()
```

## 6) Conversion rules

- Use `.execute()` when you want Mars to run the graph.
- Use `.fetch()` when you want the concrete NumPy or pandas result.
- Use `.to_numpy()` or `.to_pandas()` only when the result is small enough to
  materialize eagerly.

## 7) When to stop and route elsewhere

- Remote functions or logs -> `remote-and-scripts`.
- Learn estimators -> `learn-and-integrations`.
- Ray/GPU/Kubernetes/YARN -> `deployment-and-backends`.
