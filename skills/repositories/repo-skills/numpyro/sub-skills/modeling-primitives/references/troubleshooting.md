# Modeling-primitives troubleshooting

## `sample` outside inference needs a PRNG key

**Symptoms**

- A direct `numpyro.sample("x", dist.Normal(0, 1))` call fails or returns unexpected behavior outside a model run.
- A model trace contains no random values because it was not seeded.

**Likely cause**

JAX has no global random state. NumPyro inference algorithms and `handlers.seed` provide keys.

**Fix**

```python
from jax import random
from numpyro import handlers
tr = handlers.trace(handlers.seed(model, random.key(0))).get_trace(*args)
```

For distribution-only sampling, use `dist.Normal(0, 1).sample(random.key(0))`.

## Duplicate site names

**Symptoms**

- Error about duplicate sample/param site names.
- A trace has fewer sites than expected because a handler scoped/hid names unexpectedly.

**Likely cause**

A loop or reusable component emits the same name more than once on one execution path.

**Fix**

- Put repeated iid structure in `plate` when it is truly vectorized.
- Use `handlers.scope(prefix=...)` or unique names for repeated components.
- If using `scan`, follow its naming conventions and avoid Python-side dynamic names based on traced values.

## Plate and event shape mismatch

**Symptoms**

- Broadcasting errors inside `plate`.
- `log_prob` shape has an extra or missing observation dimension.
- A parameter inside a subsampled plate is subsampled incorrectly.

**Likely cause**

Observation axes and event axes were mixed, or `plate` dims collided.

**Fix**

1. Inspect the distribution alone in `../distributions-transforms/`.
2. Keep observation axes in `plate`; use `.to_event(k)` only for rightmost event dimensions of one observation.
3. Add explicit negative `dim` values in nested plates.
4. For `numpyro.param` inside subsampled plates, set `event_dim` so only the intended batch dimensions are subsampled.

## Python side effects or tracer errors

**Symptoms**

- `TracerBoolConversionError`, `ConcretizationTypeError`, or errors about using traced arrays in Python conditionals.
- Model works eagerly but fails under JIT, MCMC, SVI, `vmap`, or multiple chains.

**Likely cause**

Model code uses Python lists, mutation, `if`/`for` decisions on JAX arrays, non-JAX random draws, or side effects invisible to JAX.

**Fix**

- Use JAX array operations and `jax.numpy` instead of NumPy operations on traced values.
- Replace value-dependent loops/branches with `numpyro.contrib.control_flow.scan`, `cond`, or JAX control flow.
- Move plotting, downloads, logging side effects, and file writes outside model execution.

## Masked observations create an extra latent site

**Symptoms**

- A guide is missing a site named like `obs_unobserved`.
- SVI complains about a latent site introduced by masked observations.

**Likely cause**

`numpyro.sample(..., obs=..., obs_mask=mask)` conditions entries with `mask=True` and imputes the rest using a new latent site named `name + "_unobserved"`.

**Fix**

- Use `obs_mask` only when imputation is intended.
- In SVI, include the generated unobserved site in the guide or choose a different missing-data strategy.
- Do not use `obs_mask` as a general-purpose MCMC mask; use handler-level or distribution-level masking when appropriate.

## Conditioning versus substitution confusion

**Symptoms**

- A site should be observed but `is_observed` is false in the trace.
- Posterior predictive code conditions a latent site but expects it to remain sampled.

**Likely cause**

`handlers.substitute` replaces values without making sites observed; `handlers.condition` marks sample sites observed.

**Fix**

- Use `condition` for data/observations.
- Use `substitute` for fixed latent values, parameter values, or initialization probes.
- Verify with `handlers.trace(...).get_trace()` and inspect `site["is_observed"]`.

## Optional visualization dependency missing

**Symptoms**

- `render_model` fails with a Graphviz import or executable error.

**Likely cause**

Graph rendering is optional and requires Python `graphviz` plus system Graphviz tooling.

**Fix**

- Continue with `handlers.trace`, `format_shapes`, or `get_model_relations` if graph visualization is not required.
- If the user explicitly needs diagrams, install/verify Graphviz in their environment and rerun a tiny render.
