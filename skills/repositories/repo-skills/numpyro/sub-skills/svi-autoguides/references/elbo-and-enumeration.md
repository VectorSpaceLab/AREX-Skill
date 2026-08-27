# ELBO and enumeration

Choose the ELBO based on the guide/model structure, discrete latent variables, and variance-reduction needs.

## ELBO quick map

| Loss | Use when | Notes |
|---|---|---|
| `Trace_ELBO(num_particles=1, vectorize_particles=True, multi_sample_guide=False, sum_sites=True)` | Default SVI objective for many continuous-latent models. | Start here for manual guides and ordinary autoguides. Increase `num_particles` for lower-variance estimates at higher cost. |
| `TraceMeanField_ELBO(...)` | Guide is mean-field and analytic KL terms can be used. | Can be more efficient/low variance when model-guide pairs satisfy mean-field assumptions. |
| `TraceGraph_ELBO(...)` | Models with discrete latent variables where score-function variance reduction is needed. | Good when enumeration is not used or not possible but discrete sites appear. |
| `TraceEnum_ELBO(num_particles=1, max_plate_nesting=inf, vectorize_particles=True)` | Discrete latent variables can be enumerated. | Requires enumeration annotations/config and the optional `funsor` dependency. |
| `RenyiELBO(alpha=..., num_particles=...)` | Alternative Renyi objective or research workflows that need it. | Verify gradients/loss behavior on a tiny problem before using in a real analysis. |

## Discrete latent variables

For SVI with finite discrete latent variables, choose one of these strategies:

1. **Enumerate.** Mark sites with `infer={"enumerate": "parallel"}` or decorate/configure the model with `config_enumerate`, then use `TraceEnum_ELBO`. This requires Funsor.
2. **Use `TraceGraph_ELBO`.** Useful for score-function estimators/variance reduction when enumeration is not used.
3. **Marginalize manually.** Rewrite the model to sum over discrete states when tractable.
4. **Use MCMC Gibbs routes.** If sampling discrete sites is intended, route to `../mcmc-diagnostics/` for `DiscreteHMCGibbs` or `MixedHMC`.

Minimal enumeration pattern:

```python
from numpyro.contrib.funsor import config_enumerate
from numpyro.infer import SVI, TraceEnum_ELBO

@config_enumerate
def model(data):
    z = numpyro.sample("z", dist.Categorical(probs), infer={"enumerate": "parallel"})
    ...

svi = SVI(model, guide, optimizer, TraceEnum_ELBO())
```

When indexing tensors by an enumerated site, use `numpyro.ops.indexing.Vindex` to avoid incorrect broadcasting.

## `max_plate_nesting`

`TraceEnum_ELBO` needs enough enum dimensions to avoid colliding with plate dimensions. When automatic guessing fails, set `max_plate_nesting` explicitly to the number of nested vectorized plates.

```python
loss = TraceEnum_ELBO(max_plate_nesting=2)
```

If shapes are confusing, trace a short synthetic example and check plate dimensions in `../modeling-primitives/`.

## `num_particles` and vectorization

- `num_particles` averages multiple stochastic ELBO estimates.
- `vectorize_particles=True` uses vectorization where possible and is usually efficient.
- `vectorize_particles=False` can help debug shape/vectorization errors because it avoids one level of vectorized execution.
- More particles reduce estimator variance but increase memory and compute.

## Funsor optional dependency

`TraceEnum_ELBO` and `numpyro.contrib.funsor` functionality require `funsor`. Missing dependency symptoms include `ModuleNotFoundError: No module named 'funsor'` or errors mentioning Funsor imports. Use `../advanced-contrib/scripts/check_optional_dependencies.py --require funsor` or install the optional dependency in the user's environment when enumeration is required.

## Choosing between SVI and MCMC for discrete models

- Use SVI enumeration when the discrete state space is finite, structured, and tractable under plates/Markov structure.
- Use `DiscreteHMCGibbs`/`MixedHMC` when posterior sampling of discrete sites is needed and SVI approximation is not acceptable.
- If discrete branches change support or execution paths, route stochastic-support workflows to `../advanced-contrib/`.

## Validation checklist

- [ ] Every enumerated sample site has finite support.
- [ ] Enumerated sites are indexed with broadcasting-safe operations such as `Vindex`.
- [ ] `TraceEnum_ELBO` has enough plate nesting dimensions.
- [ ] `funsor` is installed and importable when enumeration is required.
- [ ] A tiny synthetic run produces finite losses before scaling to real data.
