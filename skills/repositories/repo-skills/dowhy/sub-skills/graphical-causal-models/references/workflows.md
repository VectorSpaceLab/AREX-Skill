# GCM Workflows

This reference gives self-contained DoWhy GCM workflows. It assumes the user
already has DoWhy, pandas, NumPy, and NetworkX available in the active Python
environment.

## Choose the model class

| Question | Use | Why |
|---|---|---|
| Fit a generative graph and draw observational or interventional samples | `gcm.ProbabilisticCausalModel` | Most flexible; mechanisms only need to draw conditional samples. |
| Use functional mechanisms, parent relevance, or intrinsic causal influence | `gcm.StructuralCausalModel` | Non-root mechanisms are functions of parents and noise. |
| Compute point counterfactuals from observed rows or attribute anomalies | `gcm.InvertibleStructuralCausalModel` | Noise must be recoverable from observed data. |

Do not use the GCM classes as a drop-in replacement for the classic
`CausalModel` identify/estimate/refute workflow. GCM workflows model a full
causal data-generating process and answer sampling, attribution, and
mechanism-based questions.

## Minimal graph → mechanisms → fit workflow

```python
import networkx as nx
import numpy as np
import pandas as pd
from dowhy import gcm

rng = np.random.default_rng(7)
n = 500
x = rng.normal(size=n)
t = 0.7 * x + rng.normal(scale=0.5, size=n)
y = 1.5 * t + 0.3 * x + rng.normal(scale=0.5, size=n)
data = pd.DataFrame({"X": x, "T": t, "Y": y})

graph = nx.DiGraph([("X", "T"), ("X", "Y"), ("T", "Y")])
causal_model = gcm.StructuralCausalModel(graph)
summary = gcm.auto.assign_causal_mechanisms(causal_model, data)
gcm.fit(causal_model, data)
```

Validation checks before fitting:

- `set(graph.nodes) <= set(data.columns)`.
- The graph is acyclic.
- There are no unexpected NaNs unless the workflow explicitly opts into
  experimental numerical NaN support.
- Data types reflect intent: real-valued continuous variables are numeric;
  unordered categories are represented categorically or as strings rather than
  arbitrary ordered integers.

## Automatic versus manual mechanism assignment

Use automatic assignment for quick starts and exploratory models:

```python
gcm.auto.assign_causal_mechanisms(
    causal_model,
    data,
    quality=gcm.auto.AssignmentQuality.GOOD,
)
```

Use manual assignment when domain knowledge says the mechanism class or model
family is known:

```python
from scipy.stats import norm

causal_model = gcm.StructuralCausalModel(nx.DiGraph([("X", "Y")]))
causal_model.set_causal_mechanism("X", gcm.ScipyDistribution(norm))
causal_model.set_causal_mechanism(
    "Y",
    gcm.AdditiveNoiseModel(gcm.ml.create_linear_regressor()),
)
gcm.fit(causal_model, data[["X", "Y"]])
```

For custom prediction models, implement `fit`, `predict`, and `clone`. Keep the
parent feature order deterministic. If a custom model expects named inputs,
wrap it so the array column order used by the graph is handled explicitly.

## Fit and draw observational samples

```python
gcm.fit(causal_model, data)
generated = gcm.draw_samples(causal_model, num_samples=1000)
```

The output is a pandas DataFrame with one column per graph node. Samples are
drawn by sampling roots, then propagating downstream mechanisms in topological
order. If the graph or parent sets changed since fitting, refit first.

Use the optional evaluation summary during fit for a quick mechanism-only
check:

```python
summary = gcm.fit(causal_model, data, return_evaluation_summary=True)
print(summary)
```

For deeper validation, use `evaluate_causal_model` as described in the model
validation reference.

## Interventional samples

Use interventions for forward-looking questions such as "what would happen if
we set `T` to 1?"

```python
samples = gcm.interventional_samples(
    causal_model,
    {"T": lambda _: 1.0},
    num_samples_to_draw=1000,
)
```

Rules:

- Pass exactly one of `observed_data` or `num_samples_to_draw`.
- `num_samples_to_draw` first draws observational samples from the fitted model,
  then applies the intervention and propagates downstream effects.
- `observed_data` applies interventions to the supplied rows and propagates
  affected descendants while retaining unaffected observed values.
- Intervention functions receive scalar pre-intervention values when mapped
  internally; return a scalar of compatible shape.
- Atomic interventions use `lambda _: fixed_value`. Soft interventions use
  transformations such as `lambda x: x + delta`.

## Counterfactual samples

Use counterfactuals for sample-specific alternative-past questions such as
"for this observed row, what would `Y` have been if `T` had been lower?"

```python
cf_model = gcm.InvertibleStructuralCausalModel(graph)
gcm.auto.assign_causal_mechanisms(cf_model, data)
gcm.fit(cf_model, data)

observed_row = data.iloc[[0]]
counterfactual = gcm.counterfactual_samples(
    cf_model,
    {"T": lambda _: 0.0},
    observed_data=observed_row,
)
```

Rules:

- Pass exactly one of `observed_data` or `noise_data`.
- If starting from `observed_data`, the model must be an
  `InvertibleStructuralCausalModel` so noise can be reconstructed.
- If the user already has compatible noise samples, `noise_data` can be used
  with a structural or invertible structural model.
- Point counterfactuals are strongest for continuous invertible mechanisms,
  such as additive noise models. Categorical mechanisms usually do not support
  point counterfactual reconstruction from observed data.

## Average causal effect in GCM

Use `gcm.average_causal_effect` when the user wants a difference between two
interventional regimes in the fitted GCM:

```python
ace = gcm.average_causal_effect(
    causal_model,
    target_node="Y",
    interventions_alternative={"T": lambda _: 1.0},
    interventions_reference={"T": lambda _: 0.0},
    num_samples_to_draw=1000,
)
```

Rules:

- Pass exactly one of `observed_data` or `num_samples_to_draw`.
- The target can be continuous or binary categorical. Multi-class categorical
  targets are not supported for this scalar ACE helper.
- The result is `E[target | alternative do(...)] - E[target | reference do(...)]`
  under the fitted GCM, not a classic estimator with an identified estimand.

## Runtime and sample-size controls

- Prefer small sample sizes for smoke tests; increase only for final estimates.
- For Shapley-based tasks, create a `gcm.shapley.ShapleyConfig` rather than
  relying blindly on defaults.
- Use `gcm.config.disable_progress_bars()` in scripts that should produce clean
  machine-readable output.
- Avoid nested parallelism: if a workflow uses confidence intervals around a
  Shapley-based query, keep one level of `n_jobs` at 1.
- Use `max_num_samples` in `evaluate_causal_model` when graph falsification or
  mechanism cross-validation is too slow.

## Validation checklist before trusting output

1. Confirm graph/data column alignment.
2. Print or inspect the automatic assignment summary for surprising mechanism
   choices.
3. Fit the model and, for important analyses, evaluate the causal model.
4. Check whether the task needs an invertible model; if yes, refute invertible
   assumptions when data size allows.
5. For graph-critical conclusions, run graph refutation and remember that
   non-rejection is not proof.
6. For stochastic or approximate causal queries, compute confidence intervals
   or repeat with multiple seeds and sample sizes.
7. Interpret scores in their units: variance, KL divergence, mean/variance
   change, anomaly-score contribution, or custom function output.
