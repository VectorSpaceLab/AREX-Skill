# PyMC modeling and data workflows

## Build a model with named variables

```python
import numpy as np
import pymc as pm

coords = {"obs_id": range(5), "feature": ["x1", "x2"]}
x_data = np.ones((5, 2))
y_data = np.array([0.2, 0.4, 0.1, 0.8, 0.5])

with pm.Model(coords=coords) as model:
    x = pm.Data("x", x_data, dims=("obs_id", "feature"))
    intercept = pm.Normal("intercept", 0.0, 1.0)
    beta = pm.Normal("beta", 0.0, 1.0, dims="feature")
    mu = pm.Deterministic("mu", intercept + x @ beta, dims="obs_id")
    sigma = pm.HalfNormal("sigma", 1.0)
    pm.Normal("y", mu=mu, sigma=sigma, observed=y_data, dims="obs_id")
```

Names must be unique and cannot conflict with coordinate/dimension names. `pm.Deterministic` records expressions; `pm.Potential` adds logp terms but does not affect forward sampling.

## Observed data and missing values

Observed values must be data-like and shape-compatible with the random variable. Missing observed values trigger PyMC's imputation path, creating unobserved variables such as `y_unobserved` and a deterministic with the original name. `pm.Data` itself should not be used for arrays with `nan` or masked values.

## Coordinates, dimensions, and data resizing

`coords` maps dimension names to coordinate labels or lengths. `dims` attaches dimension names to variables. Regular PyMC dims do not perform label-based alignment inside the graph; use NumPy/PyTensor broadcasting and indexing.

Use `pm.Data` for replaceable inputs:

```python
with model:
    pm.set_data({"x": new_x}, coords={"obs_id": ["new-a", "new-b"]})
```

Rules:
- Values may change shape but not rank.
- If a named dimension with coordinate labels changes length, pass replacement coordinate values.
- If multiple data containers share a dimension, update related values consistently before evaluating or sampling.
- Posterior prediction after data changes belongs to `inference-predictive`; this sub-skill owns the shape-safe mutation.

## Initial points, logp, and debug

```python
point = model.initial_point()
logp_fn = model.compile_logp()
logp_value = logp_fn(point)
```

For constrained variables, point keys may be transformed names such as `sigma_log__`. Use `sum=False` in `compile_logp` to locate bad factor contributions. Use `model.debug(point, fn="logp", verbose=True)` when initial logp is non-finite.

## `pm.do` and `pm.observe`

Use `pm.do(model, {"y": 100.0})` for interventions/counterfactuals: replace the variable mechanism/value and propagate downstream. Use `pm.observe(model, {"y": 0.5})` for conditioning on evidence. Both return new models and preserve the original model.

Replacement/observation values must have compatible shape and dtype. Constant interventions become data-like named variables by default; expressions depending on RVs become deterministics. Observing a deterministic requires PyMC to infer a logp for the underlying expression.

## Experimental `pymc.dims`

Use regular `coords`/`dims` first. Consider `pymc.dims` only for named-dimension algebra or xtensor-aware workflows and preserve the experimental API caveat in user-facing guidance.
