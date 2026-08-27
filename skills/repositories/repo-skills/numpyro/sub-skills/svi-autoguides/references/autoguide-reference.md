# Autoguide reference

Autoguides build variational guide programs automatically from the model structure. They are useful when writing a custom guide is slow or error-prone, but they still require model shapes/support to be valid.

## Selection guide

| Autoguide | Use when | Caveats |
|---|---|---|
| `AutoNormal(model, prefix='auto', init_loc_fn=..., init_scale=0.1, create_plates=None, forward_mode_differentiation=False)` | Default mean-field guide with one normal factor per latent site. | Good first choice for continuous latents; may underfit correlations. |
| `AutoDiagonalNormal(model, ...)` | Mean-field normal in a flattened latent vector. | Similar limitations to `AutoNormal`; simple and fast. |
| `AutoMultivariateNormal(model, ...)` | Capture posterior correlations with a full covariance. | Expensive for high-dimensional latents. |
| `AutoLowRankMultivariateNormal(model, rank=..., ...)` | Capture some correlations with lower memory than full covariance. | Choose rank carefully; still more expensive than diagonal. |
| `AutoDelta(model, ...)` | MAP/point-estimate style guide. | Does not represent posterior uncertainty except through downstream approximations. |
| `AutoLaplaceApproximation(model, ...)` | Fit a MAP point then approximate local Gaussian uncertainty. | Requires Hessian-like computations and can fail on nonsmooth or poorly identified models. |
| `AutoGuideList(model)` | Compose multiple guides for blocked parts of a model. | Use `handlers.block` carefully so each latent site is owned once. |
| `AutoIAFNormal` / `AutoBNAFNormal` | Flow-based flexible posterior approximations. | More parameters, more tuning, and neural-flow constraints. |
| `AutoDAIS`, `AutoSemiDAIS`, `AutoSurrogateLikelihoodDAIS` | HMC-inspired variational families for correlated or subsampled models. | Computationally expensive and have admissibility constraints; start with simpler guides. |

## Basic autoguide workflow

```python
from jax import random
import numpyro
from numpyro.infer import SVI, Trace_ELBO
from numpyro.infer.autoguide import AutoNormal


guide = AutoNormal(model)
svi = SVI(model, guide, numpyro.optim.Adam(0.01), Trace_ELBO())
result = svi.run(random.key(0), 2_000, *model_args, **model_kwargs)
params = result.params
median = guide.median(params)
quantiles = guide.quantiles(params, [0.05, 0.5, 0.95])
```

Use `Predictive(model, guide=guide, params=params, num_samples=...)` for posterior predictive samples.

## Initialization

Autoguides accept initialization functions such as `init_to_uniform`, `init_to_feasible`, `init_to_mean`, `init_to_median`, `init_to_sample`, and `init_to_value`. If the model has constrained or hard-to-initialize latents, a different `init_loc_fn` can be the difference between a finite first loss and immediate NaNs.

```python
from numpyro.infer import init_to_median
from numpyro.infer.autoguide import AutoNormal

guide = AutoNormal(model, init_loc_fn=init_to_median(num_samples=15))
```

## Blocking and guide lists

Use `AutoGuideList` when different latent groups need different guide families:

```python
from numpyro import handlers
from numpyro.infer.autoguide import AutoGuideList, AutoDelta, AutoNormal

guide = AutoGuideList(model)
guide.append(AutoDelta(handlers.block(model, expose=["global_scale"])))
guide.append(AutoNormal(handlers.block(model, hide=["global_scale"])))
```

Every latent site should be exposed to exactly one guide component. Trace a tiny model/guide pair if uncertain.

## Autoguide limitations

- Most autoguides are for continuous latent variables after support transformation.
- Discrete latent variables require enumeration, marginalization, or a different inference strategy; see [elbo-and-enumeration.md](elbo-and-enumeration.md).
- Local latent variables with subsampling can require specialized guides or DAIS variants.
- Flow and DAIS guides are heavier and can introduce their own optimization failures.
- Autoguides do not fix invalid model support, non-JAX side effects, or impossible observed values.

## When to route to MCMC

If SVI converges to a suspicious approximation or a user asks for exact-ish posterior diagnostics, route to `../mcmc-diagnostics/`. Autoguides can still help there by providing initialization or by training a transform for `NeuTraReparam`.
