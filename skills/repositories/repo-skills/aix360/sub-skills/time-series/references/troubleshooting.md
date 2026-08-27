# Time-Series Troubleshooting

Diagnose the shape and callable contract before changing model code. Run the
smallest offline fixture first and keep plotting out of the failure path.

## `input_length` and `n_variables` mismatches

**Symptoms:** `expecting input length ...`, `model requires min input length`,
`expects ... endogenous variable(s)`, or TSICE's forecast shape assertion.

**Checks and fixes:**

- Print `ts.shape`; it must be `(rows, F)`, not `(rows,)` or `(batch, rows,
  features)`.
- TSLime accepts extra rows and takes the last `input_length`; TSSaliency
  requires exactly `input_length`; TSICE accepts extra rows and takes the last
  `input_length`.
- Set `n_variables` to the number of columns in the **forecast output**, then
  verify the callable returns `(forecast_lookahead, n_variables)` for one input.
  A length-H vector is accepted only for the one-variable case.
- Do not confuse `n_exogs` with `n_variables`; the former counts related input
  columns, while the latter asserts TSICE output columns.
- For TSICE `explanation_window_length <= input_length` and an explicit
  `explanation_window_start` must be within the input range. Reduce block,
  lag, or padding settings when the chosen window is short.

## Univariate versus multivariate axes

**Symptoms:** missing-features/missing-variates errors, a reshape error, or a
returned explanation with one feature when three were expected.

Use `(T, 1)` for univariate arrays and `(T, F)` for multivariate arrays. Do not
pass `(1, T)` unless the model explicitly uses that convention and you adapt it
at the callable boundary. Keep `feature_names` length equal to `F`, and use the
same column order for the DataFrame and model wrapper. `tsFrame` requires a
2-D NumPy array even for one feature.

For TSLime, `relevant_history` changes only the time axis of the returned
weights; it does not reduce the feature axis. For TSSaliency, `saliency.shape`
must equal `input_data.shape`. For TSICE, `feature_values` contain one value per
input feature for each selected statistic, while forecast arrays use output
features.

## Scalar versus per-step model output

**TSLime/TSSaliency:** these are single-target paths. Convert a classifier's
probability vector, a multi-horizon forecast, or an anomaly score vector into
one scalar per input sample. Prefer batch `(B,1)` and single `(1,1)` outputs.
A scalar may work in sequential fallback but can stack ambiguously. If the
model only accepts flattened tensors, use a wrapper that reshapes `(B,T,F)` to
the model's expected layout and returns `(B,1)`.

**TSICE:** this is the opposite contract: return all requested forecast steps
and variables. For `H=4, n_variables=2`, return `(4,2)` for each `(T,F)` input.
Do not reduce a forecast to one scalar unless the explainer was configured with
`forecast_lookahead=1, n_variables=1` and that is the intended meaning.

**Batch fallback:** TSLime and TSSaliency first try a batch call and then warn
and call samples sequentially if it fails. Treat the warning as a performance
signal, not proof that shape semantics are correct; test both modes explicitly.

## Related/exogenous series failures

When TSICE has `n_exogs > 0`, check all of the following before calling:

```python
assert ts_related is not None
assert ts_related.shape[0] == ts.shape[0]
assert ts_related.shape[1] == n_exogs
```

The implementation passes the final `input_length + forecast_lookahead` rows of
the related frame. Make sure that future context exists and that your model
expects this exact related-window shape. TSLime and TSSaliency do not accept
`ts_related`; put required covariates in the model wrapper or the main feature
frame.

## Perturbation failures and cost

- `block-bootstrap` needs sensible `window_length` and `block_length` for the
  available rows. Start at 2 on an 8-row fixture.
- Frequency sampling can fail or become uninformative when the series is too
  short for `truncate_frequencies`; lower it or use block-bootstrap first.
- Moving-average requires a usable `lag`; shift and impute need enough rows for
  interpolation padding and blocks.
- A large `n_perturbations`, `n_samples`, or `gradient_samples` can look hung
  because the callable is being evaluated repeatedly. Begin with `N<10`,
  `n_samples=4`, and `gradient_samples=3`, then scale and record the cost.
- Set `random_seed` on TSLime/TSSaliency and `np.random.seed` around direct
  perturbation calls. A changed perturbation engine or seed changes the local
  neighborhood and can change weights/impacts.
- If a custom surrogate raises a fit error, inspect the flattened shape
  `(N, relevant_history * F)` and target shape before modifying the surrogate.

## Missing Plotly or Kaleido

TSICE's numeric result does not require a plot. Plotly is used by the example
visualizations, and Kaleido is needed for Plotly static image export. If either
is unavailable, inspect `current_forecast`, impacts, feature values, and
perturbation arrays directly or plot with an installed alternative. Do not
install or download a plotting backend just to validate numeric explanation.
A missing plotting dependency is therefore a presentation limitation, not an
explainer failure.

## No network and packaged datasets

`SunspotDataset`, `FordDataset`, and `ClimateDataset` are convenient examples,
but their constructors may acquire data when local files are absent. In a
network-restricted environment, do not call them. Use an in-memory `(T,F)`
fixture and a deterministic local model as in [workflows](workflows.md).
Network failure while obtaining a dataset is not evidence that TSICE, TSLime,
or TSSaliency is broken.

## TSSaliency instability or invalid base

- `n_samples=1` makes the implementation divide by zero; use at least 2.
- A list/array `base_value` must broadcast to the feature axis. For `F=3`, a
  three-value base is the usual form; a full `(T,F)` base is also acceptable
  if the model-specific input is intentional.
- A discontinuous model, such as a tree ensemble, can produce noisy or weak
  zeroth-order saliency. Increase samples, scale features, or use TSLime for
  model-agnostic local sensitivity instead of presenting a noisy heatmap as a
  stable gradient.
- NaNs in the input, base, or model outputs propagate into explanation values;
  validate finite numeric arrays first.

## TSICE output interpretation surprises

`data_x` and each `perturbations` entry are dictionary representations of
DataFrames, not NumPy arrays. Convert them back deliberately if needed. The
`feature_names` list describes selected statistics, while `feature_values`
contains those statistics over perturbations. `signed_impact` and
`total_impact` are one value per perturbation and are averaged over forecast
horizon/output variables. They are not direct attribution weights for each
original time step. If a per-cell explanation is required, route to TSLime or
TSSaliency.

Raw NumPy input is annotated in some internal TSICE methods, but the returned
path calls `.to_dict()` on perturbations. Use a DataFrame public input to avoid
this release-specific incompatibility.

## Safe stop conditions

Stop and report an unresolved contract instead of silently reshaping when:

- the callable's output changes rank between batch and single calls;
- the model needs future covariates that are unavailable or misaligned;
- a TSICE forecast cannot satisfy both `H` and `n_variables`;
- the intended result is certification, recourse, or a counterfactual rather
  than local explanation; or
- only a network-backed dataset is available and no local fixture can be used.
