# Effect handlers

Effect handlers reinterpret primitive statements. Compose them to trace, seed, condition, mask, reparameterize, or otherwise transform a model execution without rewriting the model.

## Core handler patterns

| Handler | Use | Pattern |
|---|---|---|
| `handlers.seed(fn, rng_seed=...)` | Thread JAX PRNG keys through random sample sites. | `seeded = handlers.seed(model, random.key(0))` |
| `handlers.trace(fn).get_trace(*args, **kwargs)` | Collect site metadata and values. | `tr = handlers.trace(handlers.seed(model, key)).get_trace(data)` |
| `handlers.condition(fn, data={"site": value})` | Turn latent sample sites into observed sites with fixed values. | `conditioned = handlers.condition(model, {"obs": y})` |
| `handlers.substitute(fn, data={"site": value})` | Replace sample or param site values without marking as observed. | Use for parameter sweeps, guide replay, or initialization. |
| `handlers.replay(fn, trace=guide_trace)` | Reuse sample values from another trace. | Common in ELBO internals and custom guide/model checks. |
| `handlers.block(fn, hide=[...], expose=[...])` | Hide selected sites from outer handlers. | Use when composing guides or excluding deterministic/helper sites. |
| `handlers.mask(fn, mask=mask)` | Mask log-probability contributions. | For model-level masking; distribution-level `d.mask` belongs in `../distributions-transforms/`. |
| `handlers.scale(fn, scale=s)` | Scale log-probability factors. | Useful for minibatch or weighted likelihoods; ensure scaling is statistically intended. |
| `handlers.reparam(fn, config={"site": Reparam()})` | Change parameterization of selected sample sites. | Route reparameterizer choice to MCMC/SVI references when used for inference. |
| `handlers.scope(fn, prefix=...)` | Prefix site names. | Helpful for composing repeated model components without duplicate names. |
| `handlers.do(fn, data={...})` | Interventional semantics for causal-style queries. | Distinguish from conditioning; interventions replace data-generating mechanisms. |

## Seed + trace inspection

```python
from jax import random
from numpyro import handlers

seeded = handlers.seed(model, random.key(0))
tr = handlers.trace(seeded).get_trace(*model_args, **model_kwargs)
for name, site in tr.items():
    print(name, site["type"], site.get("is_observed"), getattr(site.get("value"), "shape", None))
```

Useful site fields include:

- `type`: `"sample"`, `"param"`, `"deterministic"`, or `"plate"`/handler-specific entries.
- `name`: unique site name.
- `fn`: distribution object for sample sites.
- `value`: realized or observed value.
- `is_observed`: true for observed sample sites.
- `cond_indep_stack`: active plates and dimensions.
- `infer`: inference metadata such as `{"enumerate": "parallel"}`.

## Condition versus substitute

Use `condition` when a sample site becomes observed data. Use `substitute` when you are replacing a value but do not want the site marked observed.

```python
conditioned = handlers.condition(model, {"obs": y})
substituted = handlers.substitute(model, {"latent": latent_value})
```

A common debugging pattern is to condition observations and substitute latent values, then trace once to verify all deterministic outputs and shapes without running inference.

## Masking and scaling

Model-level masking:

```python
def model(y, mask):
    with numpyro.plate("N", y.shape[0]):
        with handlers.mask(mask=mask):
            numpyro.sample("obs", dist.Normal(0, 1), obs=y)
```

Scaling:

```python
with handlers.scale(scale=total_size / batch_size):
    numpyro.sample("obs", likelihood, obs=batch_y)
```

Be explicit about the statistical meaning of the scale. Do not use scaling to hide a shape error; first ensure the unscaled likelihood shape is correct.

## Reparameterization handler

`handlers.reparam(config={...})` applies reparameterizers by site name:

```python
from numpyro.infer.reparam import LocScaleReparam

with handlers.reparam(config={"theta": LocScaleReparam(centered=0.0)}):
    theta = numpyro.sample("theta", dist.Normal(mu, tau))
```

Use this when the model geometry is poor, for example hierarchical scale funnels. Route inference-specific decisions to `../mcmc-diagnostics/` or `../svi-autoguides/`.

## Composition order

Handler nesting order matters because inner handlers see primitive messages first and outer handlers see the result. Practical patterns:

```python
# Seed first, then trace the seeded execution.
trace = handlers.trace(handlers.seed(model, random.key(0))).get_trace(data)

# Condition observations, then seed remaining latent samples.
fn = handlers.seed(handlers.condition(model, {"obs": y}), random.key(1))
trace = handlers.trace(fn).get_trace(x)

# Block helper sites from a surrounding trace.
visible = handlers.trace(handlers.block(model, hide=["helper"])).get_trace(data)
```

If a handler seems ignored, check whether it is inside or outside another handler that already consumed or hid the site.
