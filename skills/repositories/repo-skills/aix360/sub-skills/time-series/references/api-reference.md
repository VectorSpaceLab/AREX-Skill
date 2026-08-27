# Time-Series API Reference

These signatures and behaviors are aligned to AIX360 0.3.0. Import the public
classes from their package modules; do not rely on example-only helpers.

## Public explainers

```python
from aix360.algorithms.tsice import TSICEExplainer
from aix360.algorithms.tslime import TSLimeExplainer
from aix360.algorithms.tssaliency import TSSaliencyExplainer

TSLimeExplainer(
    model, input_length, n_perturbations=2000, relevant_history=None,
    perturbers=None, local_interpretable_model=None, random_seed=None,
)

TSSaliencyExplainer(
    model, input_length, feature_names, base_value=None, n_samples=50,
    gradient_samples=25, gradient_function=None, random_seed=22,
)

TSICEExplainer(
    forecaster, input_length, forecast_lookahead, n_variables=1,
    n_exogs=0, n_perturbations=25, features_to_analyze=None,
    perturbers=None, explanation_window_start=None,
    explanation_window_length=10,
)
```

All three expose `get_params()` and `set_params(*argv, **kwargs)`. Call
`explainer.explain_instance(...)`; there is no separate fitting phase for the
explainer. The public calls are:

```python
TSLimeExplainer.explain_instance(self, ts, **explain_params)
TSSaliencyExplainer.explain_instance(self, ts, **explain_params)
TSICEExplainer.explain_instance(self, ts, ts_related=None, **explain_params)
```

`ts` is a time-indexed pandas `DataFrame`. TSICE calls it `tsFrame` in the
source annotations; `tsFrame` is a constructor that returns a DataFrame, not a
separate runtime class.

## TSLime result and surrogate

```python
{
    "input_data": ts,
    "model_prediction": model_prediction,
    "surrogate_prediction": surrogate_prediction,
    "history_weights": weights.reshape(relevant_history, -1),
    "x_perturbations": array,  # (n_perturbations, relevant_history, F)
    "y_perturbations": array,
}
```

The explainer first takes `xc = to_np_array(ts[-input_length:])`, generates
perturbations of shape `(N, input_length, F)`, then slices the perturbations to
the last `relevant_history` rows before fitting the surrogate. Consequently,
the returned `x_perturbations` has shape `(N, relevant_history, F)`, and
`history_weights` has shape `(relevant_history, F)` for the normal single-output
case. `relevant_history` defaults to `input_length` and must not exceed it.

The default surrogate is `LinearRegressionSurrogate`, which wraps
`sklearn.linear_model.LinearRegression`. A custom surrogate must implement the
following small interface:

```python
from aix360.algorithms.tslime.surrogate import (
    LinearSurrogateModel, LinearRegressionSurrogate, linear_surrogate_weights,
)

LinearSurrogateModel(model)
LinearSurrogateModel.fit(*args, **kwargs)
LinearSurrogateModel.predict(*args, **kwargs)
LinearSurrogateModel.get_weights()
linear_surrogate_weights(x_perturbations, y_perturbations, surrogate=None)
```

The surrogate receives flattened rows of shape `(N, relevant_history * F)` and
numeric targets. TSLime is intended for one scalar target; aggregate a vector
forecast/classifier score in the wrapper before passing it in. A model that
supports only one sample is acceptable because AIX360 falls back to sequential
calls, but a batch-capable callable is much faster.

## TSSaliency result and gradient

```python
{
    "input_data": x,                 # (T, F) NumPy array
    "saliency": normalized_score,    # (T, F)
    "feature_names": feature_names,
    "timestamps": [str(index_value), ...],
    "base_value": x_base,            # (T, F), repeated base row
    "instance_prediction": instance_predictions[0],
    "base_value_prediction": instance_predictions[1],
}
```

`feature_names` length must equal `F`. If `base_value` is omitted, the mean of
`x` across time is used, then repeated across all `T` rows. If supplied, it may
be a list or NumPy array of per-feature values; it is broadcast as a constant
signal. The implementation samples `n_samples` points on the affine path and
uses `gradient_samples` Monte Carlo directions per point. Use `n_samples >= 2`.

The default gradient is:

```python
from aix360.algorithms.tssaliency.gradient import mc_gradient_compute
mc_gradient_compute(x, fn, n_samples=10, mu=0.01, **kwargs)
```

A custom `gradient_function` must accept `x=...`, `fn=...`, and
`n_samples=...`-compatible arguments and return an array shaped like `x`.
The default function estimates gradients by zeroth-order sampling; it does not
require an autodiff backend. The model should return one scalar per sample. The
implementation warns and averages dimensions when it encounters a multi-output
result, so explicit aggregation is preferable.

## TSICE result and windows

```python
{
    "data_x": dict,                         # DataFrame.to_dict() representation
    "current_forecast": array,              # (H, n_variables)
    "feature_names": list[str],
    "feature_values": list[list[list[float]]],
    "signed_impact": list[float],
    "total_impact": list[float],
    "current_feature_values": list[array],
    "perturbations": list[dict],
    "forecasts_on_perturbations": list[array], # each (H, n_variables)
}
```

The callable contract is a single input window `(T, F)` and a forecast of shape
`(H, n_variables)`. A one-variable length-H vector is reshaped internally to
`(H, 1)`. The code asserts the first output dimension is exactly
`forecast_lookahead` and the second is exactly `n_variables`. It tries the
DataFrame input first and may fall back to a flattened tensor-style call. A
TSICE model with exogenous input is called as `model(x, x_exog)`; the exogenous
frame must have the same number of rows as `ts`, then the last `T + H` rows are
passed to the model.

`explanation_window_start=None` selects a latest window of length
`explanation_window_length` and computes `LatestFeature` statistics. A numeric
`explanation_window_start` selects that contiguous range and computes
`RangeFeature` statistics. The supported `features_to_analyze` values are:
`median`, `mean`, `min`, `max`, `std`, `range`, `intercept`, `trend`, `rsquared`,
and `max_variation`. Default is `['mean']`.

For each perturbation, TSICE computes:

- `signed_impact`: `mean(mean(f - base_f, axis=0))`, so it is signed and
  averages over horizon and output variable.
- `total_impact`: `mean(sqrt(mean((f - base_f)**2, axis=0)))`, a non-negative
  RMS-like change averaged over output variables.
- `feature_values`: each selected statistic evaluated on each perturbed input;
  a feature value normally has one value per input variate.

Use a DataFrame for TSICE even though internal annotations mention NumPy arrays:
the returned perturbations and `data_x` call `.to_dict()`, so a raw ndarray is
not a reliable public path in this release.

## Time-frame conversion

```python
from aix360.algorithms.tsutils.tsframe import tsFrame, to_np_array

tsFrame(
    df, timestamp_column=0, columns=None, freq="infer", dt=None
)
to_np_array(ts, target_vars=None)
```

`tsFrame` accepts a pandas DataFrame or a **2-D** NumPy array. For a DataFrame,
`timestamp_column` is a name or integer position; that column becomes a
`DatetimeIndex`, and `columns` optionally selects value columns. For a NumPy
array of shape `(T, F)`, it creates columns `X_1` ... `X_F` and synthetic times
using `dt` (default step 1). `to_np_array` returns a numeric `(T, F)` array and
can select DataFrame columns by names or integer positions. It rejects input
with anything other than two dimensions (a 1-D NumPy array is reshaped only in
the default-target branch, but `tsFrame` itself still requires 2-D input).

## Model wrappers

These wrappers are useful when the underlying estimator has a different method
or output shape:

```python
from aix360.algorithms.tsutils.model_wrappers import (
    Model, Anomaly_Detection_Model, Classification_Model, Forecaster,
    Tensor_Based_Classification_Model, Tensor_Based_Forecaster,
)

Model(model)
Anomaly_Detection_Model(model, scoring_function)
Classification_Model(model, class_pos=0)
Forecaster(model, forecast_function="forecast", reduce_function=None)
Tensor_Based_Classification_Model(model, class_pos=0, input_length=2, n_features=1)
Tensor_Based_Forecaster(n_features, input_length, **kwargs)
```

`Classification_Model.predict_proba` selects `class_pos` and returns `(N, 1)`;
its `predict` returns argmax class labels as `(N, 1)`. The tensor classification
wrapper reshapes flattened input to `(-1, input_length, n_features)` first.
`Anomaly_Detection_Model.predict` calls the named scoring method. `Forecaster`
calls the named forecast method, reshapes a single forecast to a column, and
reduces it with `np.mean(..., axis=0)`; in this release the configured
`reduce_function` is not used by `predict`. The tensor forecaster reshapes
before delegating. Verify the resulting scalar/forecast shape with a tiny local
call before explanation.

## Perturbation engines

The common lifecycle is `fit_transform(x, n_perturbations=1,
block_selector=None)`. The public constructors are:

```python
from aix360.algorithms.tsutils.tsperturbers import (
    BlockBootstrapPerturber, FrequencyPerturber, MovingAveragePerturber,
    TSShiftPerturber, TSImputePerturber,
)

BlockBootstrapPerturber(window_length=5, block_length=5, block_swap=2)
FrequencyPerturber(window_length=5, truncate_frequencies=5, block_length=5)
MovingAveragePerturber(window_length=5, lag=5, block_length=5)
TSShiftPerturber(max_shift=2, block_length=5, n_blocks=1,
                 interpolation_kind="linear")
TSImputePerturber(block_length=5, n_blocks=1, sparsity=1.0, padding=5,
                  interpolation_kind="linear")
```

`PerturbedDataGenerator` also accepts dictionaries with `type` values
`"block-bootstrap"`, `"frequency"`, `"moving-average"`, `"shift"`, or
`"impute"`. A list may mix dictionaries and `TSPerturber` instances. The
engines preserve `(T, F)` shape, but short windows can violate engine-specific
block, lag, padding, or frequency requirements; reduce those parameters for a
tiny fixture.
