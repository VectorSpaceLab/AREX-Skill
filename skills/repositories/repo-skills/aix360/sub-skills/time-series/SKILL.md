---
name: time-series
description: "Use AIX360 TSICE, TSLime, and TSSaliency for local numeric
  explanations of univariate or multivariate time-series models, including
  temporal perturbations, relevant history, exogenous inputs, and
  integrated-gradient saliency."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Time-Series Local Explanations

Use this sub-skill for AIX360 0.3.0 local explanations over an ordered history
window. It covers:

- **TSLime**: perturb the history, fit a local linear surrogate, and return
  time/feature weights.
- **TSSaliency**: estimate temporal and variate contributions along a path from
  a base signal using a model-agnostic Monte Carlo gradient.
- **TSICE**: perturb a selected time window and relate derived time-series
  features to changes in a multi-step forecast.
- `tsFrame`, `to_np_array`, model wrappers, perturbation engines, and numeric
  interpretation. Plotting is optional and is not part of the explanation
  contract.

## Route here when

Choose this skill when the request mentions TSICE, TSLime, TSSaliency, temporal
saliency, integrated gradients, relevant history, perturbation windows,
exogenous time-series variables, or time-series attribution. Read the
[API reference](references/api-reference.md),
[data-format contract](references/data-formats.md), and the relevant section of
[workflows](references/workflows.md) before running an explainer.

## Route elsewhere

- Generic tabular, text, or image LIME/SHAP: use
  [local-black-box](../local-black-box/SKILL.md).
- Dataset download or packaging: use
  [datasets-and-metrics](../datasets-and-metrics/SKILL.md). For offline
  explanation tests, construct an in-memory fixture instead.
- CEM, certification, or recourse: use
  [counterfactual-and-certification](../counterfactual-and-certification/SKILL.md).

## Operating contract

1. **Normalize first.** Represent a window as a pandas `DataFrame` with one row
   per time step, one numeric column per variate, and a `DatetimeIndex` (a
   `tsFrame`). A NumPy input must be two-dimensional `(time, features)` before
   conversion. Preserve column order and use the same order for
   `feature_names` and model reshaping.
2. **Fix the axes.** Record `input_length=T`, feature count `F`, and, for TSICE,
   `forecast_lookahead=H`, `n_variables=F_out`, and the exogenous count. TSLime
   accepts at least `T` rows and uses the last `T`; TSSaliency requires exactly
   `T`; TSICE accepts at least `T` and uses the last `T`.
3. **Adapt the callable.** Prefer a callable that handles batch arrays and
   returns one numeric target per sample. TSLime and TSSaliency are single-
   output explainers; aggregate a multi-output model before calling them.
   TSICE instead expects each call to return `(H, n_variables)` (or a length-H
   vector for one output). See [data formats](references/data-formats.md).
4. **Select perturbations deliberately.** Start with one small
   `block-bootstrap` engine. Add frequency, moving-average, shift, or impute
   engines only when their data assumptions fit the domain. Set a seed and use
   a small perturbation count for a smoke test; perturbation count multiplies
   model calls.
5. **Run numeric explanation before plotting.** Inspect keys and shapes, compare
   the instance and base predictions, and check that weights/saliency are
   aligned to the intended window. A plot is a presentation layer, not a
   verification gate. Plotting failures must not invalidate numeric output.
6. **Keep experiments offline by default.** Do not invoke `SunspotDataset`,
   `FordDataset`, or `ClimateDataset` merely to demonstrate the explainers:
   their constructors can download data. Use a deterministic tiny NumPy fixture
   and a local callable; see [workflows](references/workflows.md).

## Choose the explainer

| Need | Use | Main numeric result |
|---|---|---|
| Local sensitivity over recent time/feature cells | `TSLimeExplainer` | `history_weights` with shape `(relevant_history, F)` |
| Temporal/variate attribution relative to a base signal | `TSSaliencyExplainer` | `saliency` with shape `(T, F)` |
| Forecast response to structured changes in a time window | `TSICEExplainer` | perturbation responses, feature statistics, and forecast deltas |

For exact constructors, return shapes, perturbation configuration, and wrapper
behavior, use [api-reference.md](references/api-reference.md). For failures,
use [troubleshooting.md](references/troubleshooting.md) rather than silently
reshaping an input or output.

## Interpretation guardrails

- A positive TSLime weight means the local surrogate associates increasing that
  cell with increasing the selected scalar model response; it is local and
  perturbation-distribution dependent, not a causal effect.
- A positive TSSaliency value is a positive contribution under the chosen base
  signal and approximate path integral. Magnitude is comparable across cells
  only after considering feature scales and the same base/configuration.
- TSICE `signed_impact` is the average forecast change for one perturbation and
  `total_impact` is a non-negative average RMS change. The output is a sampled
  response cloud indexed by derived statistics, not a guaranteed per-feature
  coefficient.
- For multi-step or multi-variable forecasts, always state whether a summary
  averages horizons/variables. A scalar summary can hide cancellation.

Do not use these explainers as certification, recourse, or counterfactual
proof. Do not claim that a heatmap is an attribution result unless its numeric
source and axes have been checked.
