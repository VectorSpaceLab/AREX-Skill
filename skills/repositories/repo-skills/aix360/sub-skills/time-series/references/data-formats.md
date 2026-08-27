# Time-Series Data and Model Shapes

Treat the time axis and feature axis as separate contracts. Most difficult
failures in these explainers come from passing a vector where AIX360 expects a
matrix, using a batch-shaped tensor for a single call, or naming a different
number of features than the callable actually consumes.

## Canonical frame

Use a pandas `DataFrame` with:

- rows in chronological order, shape `(T, F)`;
- numeric values and no accidental timestamp column among the model features;
- one column per variate, in the exact order expected by the model;
- a `DatetimeIndex` when using `tsFrame` or a public explainer.

```python
import numpy as np
import pandas as pd
from aix360.algorithms.tsutils.tsframe import tsFrame, to_np_array

values = np.arange(12, dtype=float).reshape(6, 2)
ts = tsFrame(values)                 # DataFrame, shape (6, 2)
assert to_np_array(ts).shape == (6, 2)

raw = pd.DataFrame({
    "time": pd.date_range("2024-01-01", periods=6, freq="h"),
    "signal": values[:, 0],
    "context": values[:, 1],
})
ts = tsFrame(raw, timestamp_column="time", columns=["signal", "context"])
```

`tsFrame` on a NumPy array requires 2-D input. For a univariate series, use
shape `(T, 1)`, not `(T,)`. A DataFrame with one value column is the clearest
univariate representation. `to_np_array` yields `(T, F)` and retains column
order unless `target_vars` explicitly selects columns.

The index values are carried into TSSaliency's `timestamps` output as strings.
The explainers use row positions for windows; they do not resample or infer
missing time steps. Validate ordering and sampling regularity before explaining
if those properties matter to the model.

## Window and feature axes

Let:

- `T` = configured model history `input_length`;
- `F` = number of input variates/columns;
- `H` = TSICE forecast lookahead;
- `F_out` = number of TSICE forecast variables;
- `N` = perturbation count;
- `R` = TSLime `relevant_history`.

| Component | Input window | Callable input(s) | Required result |
|---|---:|---|---|
| TSLime | at least `T` rows; last `T` are used | batch `(N,T,F)` and preferably single `(T,F)` | one scalar per sample, preferably `(N,1)` |
| TSSaliency | exactly `T` rows | batch `(B,T,F)` for instance/base and gradient samples | one scalar per sample; gradient result `(T,F)` |
| TSICE | at least `T` rows; last `T` are used | single `(T,F)` | `(H,F_out)`; one-output vector `(H,)` is reshaped |

For TSLime the perturbations are sliced to the last `R` rows before the
surrogate is fitted. Thus the usual outputs are:

```text
x_perturbations       (N, R, F)
y_perturbations        (N, 1)
history_weights        (R, F)
```

For TSSaliency:

```text
input_data             (T, F)
base_value             (T, F)
saliency                (T, F)
```

For TSICE:

```text
current_forecast       (H, F_out)
feature_values[j]      (N, F)       # for each selected statistic j
current_feature_values[j] (F,)
forecasts_on_perturbations[i] (H, F_out)
signed_impact          (N,)
total_impact            (N,)
```

`n_variables` in TSICE is an output-shape assertion as well as an input
configuration in the surrounding time-series contract. For a normal
same-variable forecast use `n_variables=F`. If the model returns a different
number of output variables, set it explicitly and check the semantics of
`current_forecast` before interpreting impacts.

## Callable adapters

A robust scalar wrapper handles both batch and single-window calls:

```python
def scalar_model(x):
    a = np.asarray(x, dtype=float)
    if a.ndim == 2:                  # one window: (T, F)
        return np.array([[a.mean()]])
    if a.ndim == 3:                  # batch: (B, T, F)
        return a.mean(axis=(1, 2), keepdims=False).reshape(-1, 1)
    raise ValueError("expected (T,F) or (B,T,F)")
```

Use this shape discipline for both TSLime and TSSaliency. A callable that
returns a Python float for one window may work in sequential fallback, but a
consistent `(1, 1)` result avoids ambiguous stacking. A callable returning a
vector of class probabilities or a forecast should be wrapped to select or
aggregate one scalar before TSLime/TSSaliency. Do not let a hidden `squeeze()`
turn `(B,1)` into a scalar when `B=1`.

For TSICE, keep forecast axes explicit:

```python
def forecaster(x):
    a = np.asarray(x, dtype=float)
    level = a.mean(axis=0)             # (F,)
    return np.repeat(level[None, :], repeats=2, axis=0)  # (H=2, F)
```

If the forecaster consumes a flattened tensor, the implementation may fall
back to a flattened shape. It is safer to adapt the callable yourself and test
one `(T,F)` call than to rely on exception-driven detection.

## Exogenous variables

TSICE's public call is:

```python
explanation = explainer.explain_instance(ts, ts_related=exog)
```

When `n_exogs > 0`, `exog` must be non-null, have exactly `n_exogs` columns,
and have the same number of rows as `ts`. AIX360 slices the final `T + H` rows
of the related frame before passing them with the final `T` endogenous rows.
Keep timestamps aligned and document whether the model expects the extra
future rows. TSLime and TSSaliency do not expose a related-series argument in
this release; combine any required covariates into the columns of `ts` or
write a callable wrapper that supplies them.

A subtle implementation detail: TSICE perturbs the endogenous window and keeps
the supplied exogenous frame fixed for each forecast call. Therefore its impact
should be described as sensitivity to the perturbed endogenous history
conditional on those exogenous values, not as joint attribution of both sets.

## Numeric output versus plots

The numeric explanation is valid without Plotly, Kaleido, or interactive plotting:

- plot TSLime weights as a bar chart indexed by the last `R` timestamps;
- plot TSSaliency as a `(T,F)` heatmap or one line per feature;
- plot TSICE perturbation feature values against `signed_impact` or
  `total_impact`, and optionally overlay `current_forecast` and perturbed
  forecasts.

Keep the array-to-axis mapping explicit. For a univariate result, retain the
singleton feature dimension until the final presentation step. For a
multivariate result, never flatten `(T,F)` without recording which feature each
block belongs to.

## Offline tiny fixtures

Use an in-memory deterministic frame for smoke tests. Six to twelve rows, one
to three columns, `block_length=2`, `window_length=2`, and fewer than ten
perturbations are enough to verify axes. Avoid the packaged dataset loaders in
an offline check: Sunspots, Ford, and Climate loaders are data acquisition
utilities, not required inputs to the explainers.
