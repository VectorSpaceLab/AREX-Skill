# Time-Series Explanation Workflows

The workflows below use local numeric fixtures and keep plotting optional. Start
with the smallest configuration that proves the model/input contract, then
increase sampling only after the shapes and interpretation are correct.

## 1. Build and validate a frame

```python
import numpy as np
from aix360.algorithms.tsutils.tsframe import tsFrame, to_np_array

T, F = 8, 2
values = np.arange(T * F, dtype=float).reshape(T, F) / 10.0
ts = tsFrame(values)
assert ts.shape == (T, F)
assert to_np_array(ts).shape == (T, F)
```

For real local data, convert the timestamp column once and preserve the
resulting column order. Do not pass the raw timestamp as a model variate.
Before an explainer call, assert `len(ts) >= input_length` and that all values
are finite. TSSaliency additionally requires `len(ts) == input_length`.

## 2. TSLime: recent history weights

TSLime is the default choice for model-agnostic local sensitivity. Aggregate a
multi-output predictor to one scalar and make it accept both batch and single
window inputs where possible:

```python
import numpy as np
from aix360.algorithms.tslime import TSLimeExplainer
from aix360.algorithms.tsutils.tsperturbers import BlockBootstrapPerturber

def score(x):
    a = np.asarray(x, dtype=float)
    if a.ndim == 2:
        return np.array([[a.sum()]])
    return a.sum(axis=(1, 2)).reshape(-1, 1)

R = 3
explainer = TSLimeExplainer(
    model=score,
    input_length=T,
    relevant_history=R,
    n_perturbations=8,
    perturbers=[BlockBootstrapPerturber(window_length=2, block_length=2,
                                        block_swap=1)],
    random_seed=7,
)
result = explainer.explain_instance(ts)
assert result["history_weights"].shape == (R, F)
assert result["x_perturbations"].shape == (8, R, F)
```

Read `history_weights` in the original feature order. Use the last `R` rows of
`ts` for labels/plots. `model_prediction` and `surrogate_prediction` are
numeric checks of the local approximation; a large disagreement means the
surrogate or perturbation neighborhood is not faithful enough for a strong
interpretation. Increase `n_perturbations`, change the perturbation engine, or
reduce `relevant_history` only after investigating that disagreement.

A custom surrogate is passed as `local_interpretable_model`; it must expose
`fit`, `predict`, and `get_weights`. The fitted surrogate receives flattened
`(R*F)` columns, not a 3-D tensor.

## 3. TSSaliency: base-relative temporal attribution

Use TSSaliency when the question is contribution relative to a reference signal:

```python
from aix360.algorithms.tssaliency import TSSaliencyExplainer

def score(x):
    a = np.asarray(x, dtype=float)
    if a.ndim == 2:
        return np.array([[a.sum()]])
    return a.sum(axis=(1, 2)).reshape(-1, 1)

explainer = TSSaliencyExplainer(
    model=score,
    input_length=T,
    feature_names=["signal", "context"],
    n_samples=4,
    gradient_samples=3,
    random_seed=7,
)
result = explainer.explain_instance(ts)
assert result["saliency"].shape == (T, F)
assert result["base_value"].shape == (T, F)
```

The default base is a constant per-feature mean. To use a domain baseline,
pass `base_value=[value_for_signal, value_for_context]` (or a compatible array)
to `explain_instance`, or set it in the constructor. Inspect both
`instance_prediction` and `base_value_prediction` before interpreting signs.
The result is an approximate integrated-gradient-style attribution; it is not a
causal intervention and can be unstable for discontinuous or tree ensemble
models. For a differentiable model, a custom gradient function can be supplied
when the model's batching contract is known.

The source computes `dt = 1/(n_samples-1)`, so `n_samples=1` is invalid. A
small `gradient_samples` is suitable only for smoke tests; raise it for a more
stable estimate and report the setting.

## 4. TSICE: structured forecast perturbations

Use TSICE for a forecast response cloud rather than a single per-cell weight:

```python
import numpy as np
from aix360.algorithms.tsice import TSICEExplainer
from aix360.algorithms.tsutils.tsperturbers import BlockBootstrapPerturber

def forecast(x):
    a = np.asarray(x, dtype=float)
    level = a.mean(axis=0)
    return np.repeat(level[None, :], repeats=2, axis=0)  # (H=2, F)

explainer = TSICEExplainer(
    forecaster=forecast,
    input_length=T,
    forecast_lookahead=2,
    n_variables=F,
    explanation_window_length=3,
    explanation_window_start=None,       # latest three rows
    features_to_analyze=["mean", "trend"],
    n_perturbations=8,
    perturbers=[BlockBootstrapPerturber(window_length=2, block_length=2,
                                        block_swap=1)],
)
result = explainer.explain_instance(ts)
assert np.asarray(result["current_forecast"]).shape == (2, F)
assert len(result["signed_impact"]) == 8
assert np.asarray(result["forecasts_on_perturbations"]).shape == (8, 2, F)
```

Use `explanation_window_start=<nonnegative index>` with
`explanation_window_length` to analyze a range, or `None` to analyze the latest
window. Supported statistics include `mean`, `median`, `min`, `max`, `std`,
`range`, `intercept`, `trend`, `rsquared`, and `max_variation`. A statistic is
computed per input feature. Compare its values against `signed_impact` or
`total_impact`; do not label a correlation in this sampled cloud as a causal
feature effect.

For exogenous inputs, construct an aligned `ts_related` frame with exactly
`n_exogs` columns and the same row count as `ts`, then call
`explain_instance(ts, ts_related=ts_related)`. Keep the forecast output contract
explicit because TSICE asserts both forecast dimensions.

## 5. Perturber selection and cost

The generator samples across the configured engines. A list of multiple engines
is a mixture of perturbation mechanisms, not a sequence of transformations.
Use one engine first to make the neighborhood interpretable:

- `block-bootstrap`: exchanges residual blocks; a practical default for short
  local smoke tests.
- `frequency`: changes residual spectra and can require a suitable length for
  sampled frequencies.
- `moving-average`: creates moving-average-style residual noise; `lag` and
  window must fit the history.
- `shift`: shifts continuous blocks and interpolates them.
- `impute`: removes blocks and interpolates from surrounding observations.

For TSLime, model evaluations are approximately `N` for perturbations plus a
prediction of the instance. For TSSaliency, path sampling and Monte Carlo
sampling can require on the order of `n_samples * (gradient_samples + 1)` model
calls, in addition to base/instance predictions. TSICE evaluates the base and
one forecast per perturbation. Batch-capable callables reduce overhead but do
not change the conceptual cost.

Set `np.random.seed(...)` for direct perturbation checks and use each explainer's
`random_seed` for TSLime/TSSaliency. Repeated runs with the same seed, data,
model, and configuration should be compared before drawing conclusions.

## 6. Numeric inspection and optional plots

A minimal numeric review should record:

1. input shape and column order;
2. configured `T`, `F`, `R`, and, for TSICE, `H`/`n_variables`;
3. model output shape on a single window and a batch;
4. explanation output shapes and finite-value checks;
5. seed, perturbation engine, and sample counts;
6. prediction/base or surrogate agreement where applicable.

Only after that, use the plotting library of choice:

- TSLime: bars of `history_weights[:, feature]` over the final `R` times;
- TSSaliency: a signed heatmap or feature-separated temporal lines;
- TSICE: feature-value versus impact scatter/line plots and forecast overlays.

The examples' Plotly/Kaleido helpers are not required for these numeric steps.
If plotting is unavailable, save arrays or use plain pandas/matplotlib; do not
rerun explanation solely to obtain an image.

## Difficult synthetic verification cases

Use these cases for sub-skill verification beyond the repository's dataset-
backed tests:

1. **Multivariate scalar-output case:** a deterministic `(T,3)` frame and a
   callable that accepts `(B,T,3)` but returns `(B,1)`. Verify TSLime returns
   `(R,3)`, TSSaliency returns `(T,3)`, and no feature axis is silently
   flattened or dropped.
2. **Forecast/window/exog case:** a `(T+4,2)` endogenous frame, a matching
   exogenous frame with two columns, and a TSICE callable returning `(H,2)`.
   Test both latest and explicit range windows, then deliberately set a wrong
   `n_variables` or exog width and verify a clear failure before plotting.
