# Modeling primitives

Read this when a task is about the structure of a NumPyro model program rather than the distribution object or inference algorithm.

## Mental model

A NumPyro model is an ordinary Python callable that uses primitive statements. Inference algorithms and effect handlers give those statements meaning. Keep the callable as pure and JAX-compatible as possible: no hidden global random state, avoid side effects that JAX cannot see, and make data/model arguments explicit.

```python
from jax import random
import jax.numpy as jnp
import numpyro
import numpyro.distributions as dist


def model(x, y=None):
    weight = numpyro.sample("weight", dist.Normal(0.0, 1.0))
    bias = numpyro.sample("bias", dist.Normal(0.0, 1.0))
    logits = weight * x + bias
    numpyro.deterministic("mean_prob", jnp.mean(jax.nn.sigmoid(logits)))
    with numpyro.plate("data", x.shape[0]):
        numpyro.sample("obs", dist.Bernoulli(logits=logits), obs=y)
```

## Public primitive quick reference

| Primitive | Use | Important arguments and gotchas |
|---|---|---|
| `numpyro.sample(name, fn, obs=None, rng_key=None, sample_shape=(), infer=None, obs_mask=None)` | Declare a latent or observed random variable. | `fn` is usually a `numpyro.distributions.Distribution`. Inside a model, `handlers.seed` or an inference algorithm supplies keys; `rng_key` is mostly for sample calls outside an active handler stack. `infer={"enumerate": "parallel"}` marks finite discrete sites for enumeration. `obs_mask` creates an additional latent site named `name + "_unobserved"` and is not intended for MCMC. |
| `numpyro.param(name, init_value=None, constraint=constraints.real, event_dim=None)` | Declare an optimizable parameter, usually in a guide. | There is no global parameter store. In SVI, parameters live in the SVI state. Callable initializers require a `handlers.seed` context. Use constraints for positive/simplex/etc. guide parameters. |
| `numpyro.plate(name, size, subsample_size=None, dim=None)` | Mark conditionally independent batch dimensions. | Use for iid observation axes. Pick explicit negative `dim` values in complex nested models to avoid collisions. `subsample_size` introduces minibatching semantics; use `numpyro.subsample` for arrays. |
| `numpyro.plate_stack(prefix, sizes, rightmost_dim=-1)` | Create a stack of plates. | Useful for multi-axis independent structure when dims are regular. |
| `numpyro.deterministic(name, value)` | Record a deterministic quantity in traces and posterior samples. | Most handlers do not change deterministic sites. MCMC summaries may exclude deterministic values unless requested. |
| `numpyro.factor(name, log_factor)` | Add an arbitrary log-density term. | Use carefully: `log_factor` must be a JAX array scalar or broadcastable term with correct plate context. |
| `numpyro.module`, `flax_module`, `nnx_module`, `eqx_module` | Register neural-module parameters. | Core `module` is for stax-style tuples. Flax/NNX/Equinox wrappers require optional dependencies; route detailed use to `../advanced-contrib/`. |
| `numpyro.prng_key()` | Read the current handler-provided key. | Returns a key only inside a seeded context; use sparingly and prefer explicit arguments when possible. |
| `numpyro.subsample(data, event_dim=0)` | Select a minibatch slice inside a subsampled plate. | `event_dim` says how many rightmost dims belong to each observation/event. |

## PRNG and seeding rules

Unlike libraries with a global random state, JAX requires explicit PRNG keys. NumPyro inference algorithms and `handlers.seed` thread keys through model execution.

Safe patterns:

```python
from jax import random
from numpyro import handlers

# Sample outside inference by seeding the model.
seeded = handlers.seed(model, random.key(0))
trace = handlers.trace(seeded).get_trace(x, y)

# Direct distribution sampling also needs a key.
z = dist.Normal(0.0, 1.0).sample(random.key(1), sample_shape=(10,))
```

Avoid relying on `numpyro.sample("x", dist.Normal(0, 1))` outside a seeded model or inference context. If there is no active handler stack and no `rng_key`, random sampling cannot happen.

## Plates and observation axes

Use `plate` for conditionally independent observations and keep vector-valued observations as event dimensions in the distribution object.

```python
def regression(x, y=None):
    beta = numpyro.sample("beta", dist.Normal(0, 1).expand((x.shape[1],)).to_event(1))
    sigma = numpyro.sample("sigma", dist.HalfNormal(1.0))
    mean = x @ beta
    with numpyro.plate("rows", x.shape[0]):
        numpyro.sample("obs", dist.Normal(mean, sigma), obs=y)
```

When shapes fail:

1. Outside the model, inspect `dist.batch_shape`, `dist.event_shape`, and `dist.log_prob(example).shape` in `../distributions-transforms/`.
2. Inside the model, ensure each observation axis has exactly one plate and each event axis is consumed by the distribution.
3. Use explicit `dim=-1`, `dim=-2`, etc. in nested plates when automatic placement is ambiguous.

## Subsampling

Subsampling is a model-level statement, not just array slicing:

```python
def model(data):
    n = data.shape[0]
    with numpyro.plate("N", n, subsample_size=128):
        batch = numpyro.subsample(data, event_dim=1)
        numpyro.sample("obs", dist.Normal(0.0, 1.0), obs=batch[:, 0])
```

Subsampling affects likelihood scaling and introduces plate metadata used by algorithms such as HMCECS. Do not replace it with arbitrary Python slicing unless you also account for likelihood scaling.

## JAX-compatible control flow

Use ordinary Python control flow for static branches known before tracing. Use NumPyro/JAX control flow when values are traced, vectorized, or time-indexed:

- `numpyro.contrib.control_flow.scan` for recurrent/state-space/time-series models. It preserves effect-handler semantics across a scanned transition.
- `numpyro.contrib.control_flow.cond` for JAX-traceable conditional branches.

If a model raises tracer errors around dynamic list appends, Python `if` statements on JAX arrays, or mutation inside loops, convert the state to explicit JAX arrays and route the loop through `scan` or `lax`-style control flow.

## Minimal pre-inference checklist

- [ ] Model and guide call signatures accept the same data arguments when used in SVI.
- [ ] Every sample/param/deterministic site name is unique in one execution path.
- [ ] Observed values have shapes compatible with distribution `batch_shape + event_shape` and plate context.
- [ ] No hidden network downloads, file writes, or non-JAX random draws happen during model execution.
- [ ] The model can be seeded and traced on a tiny input before running MCMC/SVI.
