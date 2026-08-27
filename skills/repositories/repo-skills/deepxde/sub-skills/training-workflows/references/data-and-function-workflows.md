# Function, tabular dataset, and multifidelity workflows

This reference covers DeepXDE data classes that are trained through the generic `dde.Model(data, net)` lifecycle. It does not cover PDE residual/BC construction or DeepONet operator datasets.

## `dde.data.Function`: learn a formula sampled on a geometry

Signature:

```python
dde.data.Function(
    geometry,
    function,
    num_train,
    num_test,
    train_distribution="uniform",
    online=False,
)
```

Contract:

- `geometry` is a DeepXDE geometry object such as `dde.geometry.Interval(a, b)`.
- `function(x)` receives a NumPy array with shape `(N, input_dim)` and returns a NumPy array with shape `(N, output_dim)`.
- `num_train` points are sampled inside/on the geometry for training; `num_test` uniform points are used for test/evaluation.
- `train_distribution` can be `"uniform"`, `"pseudo"`, `"LHS"`, `"Halton"`, `"Hammersley"`, or `"Sobol"`.
- `online=True` resamples training points on every training step and forces pseudorandom sampling if another distribution was requested.

Recipe:

```python
import numpy as np
import deepxde as dde

def f(x):
    return x * np.sin(5 * x)

geom = dde.geometry.Interval(-1, 1)
data = dde.data.Function(geom, f, num_train=32, num_test=200)
net = dde.nn.FNN([1, 32, 32, 1], "tanh", "Glorot uniform")
model = dde.Model(data, net)
model.compile("adam", lr=1e-3, metrics=["l2 relative error"])
losshistory, train_state = model.train(iterations=1000, display_every=100)
```

Use this class for analytic functions and cheap synthetic regression targets. Use `DataSet` when you already have arrays or files.

## `dde.data.DataSet`: fit array or text-file data

Signature:

```python
dde.data.DataSet(
    X_train=None,
    y_train=None,
    X_test=None,
    y_test=None,
    fname_train=None,
    fname_test=None,
    col_x=None,
    col_y=None,
    standardize=False,
)
```

Two input modes are supported:

1. **Array mode**: provide `X_train`, `y_train`, `X_test`, and `y_test` as NumPy arrays.
2. **Text-file mode**: provide `fname_train`, `fname_test`, `col_x`, and `col_y`; DeepXDE loads files with `np.loadtxt` and slices columns.

Shape and column rules:

| Field | Expected shape or value |
| --- | --- |
| `X_train` | `(n_train, input_dim)` floating array |
| `y_train` | `(n_train, output_dim)` floating array |
| `X_test` | `(n_test, input_dim)` floating array |
| `y_test` | `(n_test, output_dim)` floating array |
| `col_x` | list/tuple of input column indices, e.g. `(0,)` or `(0, 2)` |
| `col_y` | list/tuple of output column indices, e.g. `(1,)` |
| `standardize=True` | Standardizes inputs only, storing `scaler_x`; use `data.transform_inputs(x_new)` before predicting external points. |

Array recipe:

```python
X_train = np.linspace(-1, 1, 64)[:, None]
y_train = X_train * np.sin(5 * X_train)
X_test = np.linspace(-1, 1, 128)[:, None]
y_test = X_test * np.sin(5 * X_test)

data = dde.data.DataSet(X_train, y_train, X_test, y_test, standardize=True)
net = dde.nn.FNN([1, 32, 32, 1], "tanh", "Glorot normal")
model = dde.Model(data, net)
model.compile("adam", lr=1e-3, metrics=["l2 relative error"])
model.train(iterations=1000)
y_pred = model.predict(data.transform_inputs(X_test))
```

Text-file recipe:

```python
data = dde.data.DataSet(
    fname_train="train.txt",
    fname_test="test.txt",
    col_x=(0,),
    col_y=(1,),
    standardize=True,
)
```

`DataSet.train_next_batch()` returns the full training arrays in this version; `Model.train(batch_size=...)` does not create true mini-batches for this class.

## Multifidelity workflows

DeepXDE provides two generic multifidelity data classes. They are normally paired with multifidelity-capable networks such as `dde.nn.MfNN` when that network is available for the selected backend. The source examples advertise the formula and dataset MFNN workflows for TensorFlow v1 compatibility and Paddle; this construction did not verify them on PyTorch CPU.

### `dde.data.MfFunc`: low/high-fidelity formulas

Signature:

```python
dde.data.MfFunc(geom, func_lo, func_hi, num_lo, num_hi, num_test, dist_train="uniform")
```

Contract:

- `func_lo(x)` and `func_hi(x)` receive the same `(N, input_dim)` NumPy array and return `(N, output_dim)` arrays.
- Training inputs stack `num_lo` low-fidelity points and `num_hi` high-fidelity points.
- Targets are a two-element list `[y_lo_train, y_hi_train]`.
- Training loss contains two components: low-fidelity loss on the low slice and high-fidelity loss on the high slice.

Skeleton:

```python
def lo(x):
    return 0.5 * (6 * x - 2) ** 2 * np.sin(12 * x - 4) + 10 * (x - 0.5) - 5

def hi(x):
    return (6 * x - 2) ** 2 * np.sin(12 * x - 4)

geom = dde.geometry.Interval(0, 1)
data = dde.data.MfFunc(geom, lo, hi, num_lo=100, num_hi=6, num_test=1000)
# Build a backend-compatible multifidelity net before Model(data, net).
```

### `dde.data.MfDataSet`: low/high-fidelity arrays or text files

Signature:

```python
dde.data.MfDataSet(
    X_lo_train=None,
    X_hi_train=None,
    y_lo_train=None,
    y_hi_train=None,
    X_hi_test=None,
    y_hi_test=None,
    fname_lo_train=None,
    fname_hi_train=None,
    fname_hi_test=None,
    col_x=None,
    col_y=None,
    standardize=False,
)
```

Shape and column rules:

| Field | Expected shape or value |
| --- | --- |
| `X_lo_train` | `(n_lo, input_dim)` low-fidelity inputs |
| `y_lo_train` | `(n_lo, output_dim)` low-fidelity targets |
| `X_hi_train` | `(n_hi, input_dim)` high-fidelity inputs |
| `y_hi_train` | `(n_hi, output_dim)` high-fidelity targets |
| `X_hi_test` / `y_hi_test` | high-fidelity test arrays only |
| `fname_lo_train`, `fname_hi_train`, `fname_hi_test` | text files read with `np.loadtxt` |
| `col_x`, `col_y` | column index lists/tuples used for every supplied file |
| `standardize=True` | Standardizes low/high inputs together and transforms high-fidelity test inputs. |

Implementation detail that matters for debugging: `MfDataSet.train_next_batch()` vertically stacks low- and high-fidelity input arrays, then constructs two target arrays with zero padding so low and high losses can index their respective slices. Shape mismatches between low and high input dimensions or output dimensions therefore surface during stacking or loss computation.

## Choosing a data class

| User need | Use | Avoid |
| --- | --- | --- |
| Learn a known formula over a DeepXDE geometry | `Function` | `DataSet` unless samples already exist |
| Learn from in-memory NumPy arrays | `DataSet` array mode | `Function` unless a callable target is available |
| Learn from plain numeric text files | `DataSet` file mode | Hard-coded relative files without checking `cwd` |
| Low/high-fidelity formula learning | `MfFunc` + backend-compatible MFNN | Assuming PyTorch support without verifying network availability |
| Low/high-fidelity data files/arrays | `MfDataSet` + backend-compatible MFNN | Mixing low/high dimensions or output widths |
| Operator learning with branch/trunk data | Operator sub-skill | Treating operator labels as ordinary `DataSet` rows |

## Validation checklist before training

- Set the backend before importing DeepXDE if you need a specific backend.
- Make all arrays two-dimensional, even for scalar inputs/outputs: use `x[:, None]` and `y[:, None]`.
- Match the first dimension of each `X_*` and `y_*` pair.
- Match `net` input width to `X` column count or geometry dimension.
- Match `net` output width to target output dimension or to the multifidelity network contract.
- If `standardize=True`, transform new prediction inputs with `data.transform_inputs(x)` for `DataSet` workflows.
- In headless runs, do not request plots; use `dde.saveplot(..., isplot=False)` or skip plotting.
