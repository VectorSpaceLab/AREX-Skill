# SVI workflows

This reference covers the practical flow for fitting a NumPyro model with `SVI`. It assumes the model itself can be seeded/traced on tiny data and that distribution support/shape issues are already understood.

## Minimal manual-guide workflow

```python
from jax import random
import jax.numpy as jnp
import numpyro
import numpyro.distributions as dist
from numpyro.distributions import constraints
from numpyro.infer import SVI, Trace_ELBO


def model(data):
    p = numpyro.sample("p", dist.Beta(1.0, 1.0))
    with numpyro.plate("N", data.shape[0]):
        numpyro.sample("obs", dist.Bernoulli(p), obs=data)


def guide(data):
    alpha_q = numpyro.param("alpha_q", 1.0, constraint=constraints.positive)
    beta_q = numpyro.param("beta_q", 1.0, constraint=constraints.positive)
    numpyro.sample("p", dist.Beta(alpha_q, beta_q))

optimizer = numpyro.optim.Adam(step_size=0.01)
svi = SVI(model, guide, optimizer, loss=Trace_ELBO())
result = svi.run(random.key(0), 2_000, data, progress_bar=True)
params = result.params
losses = result.losses
```

Key rule: guide sample sites should cover the model's latent sample sites for ordinary ELBOs. Guide `param` sites should use constraints matching their intended support.

## `SVI` API operations

The inspected public constructor is:

```python
SVI(model, guide, optim, loss, **static_kwargs)
```

Core operations:

| API | Use | Notes |
|---|---|---|
| `svi.init(rng_key, *args, init_params=None, **kwargs)` | Initialize optimizer state and unconstrained guide params. | Use when you need a custom update loop. `init_params` overrides initial `param` values. |
| `svi.update(state, *args, **kwargs)` | Take one optimization step. | Returns `(new_state, loss)`. Loss should be finite. |
| `svi.evaluate(state, *args, **kwargs)` | Evaluate loss without updating. | Useful for validation/held-out checks. |
| `svi.get_params(state)` | Return constrained parameter values. | Use this for reporting and `Predictive`; do not inspect unconstrained optimizer internals. |
| `svi.run(rng_key, num_steps, *args, progress_bar=True, stable_update=False, init_params=None, **kwargs)` | Convenience loop. | Returns `SVIRunResult(params, state, losses)`. Use `stable_update=True` when you want to skip updates that produce non-finite loss/params. |

## Optimizers

NumPyro optimizers include `Adam`, `ClippedAdam`, `Adagrad`, `Momentum`, `RMSProp`, `RMSPropMomentum`, `SGD`, `SM3`, and `Minimize`.

```python
optimizer = numpyro.optim.ClippedAdam(step_size=1e-3, clip_norm=10.0)
```

`SVI` can also accept a JAX example-libraries optimizer or an Optax `GradientTransformation`. If an Optax optimizer is passed and `optax` is missing, NumPyro raises an import error explaining that Optax must be installed.

```python
# Optional dependency path.
import optax
svi = SVI(model, guide, optax.chain(optax.clip(10.0), optax.adam(1e-3)), Trace_ELBO())
```

## Custom update loop

Use a manual loop when you need custom logging, minibatches, validation, or early stopping:

```python
state = svi.init(random.key(0), train_data)
for step in range(num_steps):
    state, loss = svi.update(state, train_data)
    if step % 100 == 0:
        print(step, float(loss))
params = svi.get_params(state)
```

For minibatches, ensure the model uses `plate(..., subsample_size=...)` or an equivalent statistically correct scaling strategy. Arbitrary data slicing without likelihood scaling can bias the objective.

## Posterior and predictive samples from SVI

```python
from numpyro.infer import Predictive

# Sample latent sites from the guide.
guide_predictive = Predictive(guide, params=params, num_samples=1_000)
posterior_latents = guide_predictive(random.key(1), data=None)

# Simulate from the model using the guide distribution.
model_predictive = Predictive(model, guide=guide, params=params, num_samples=1_000)
posterior_predictive = model_predictive(random.key(2), data=None)
```

If using an autoguide, its `median(params)`, `quantiles(params, quantiles)`, or call semantics may provide additional summaries. Use the autoguide reference for guide-specific details.

## Validation checklist

- [ ] Model and guide accept the same dynamic arguments.
- [ ] Every continuous latent in the model has a guide sample site, unless an autoguide owns it.
- [ ] Discrete latents use an ELBO that can handle them, or they are enumerated/summed out.
- [ ] `losses` are finite and generally improve on a smoke problem.
- [ ] `params` returned by `get_params` satisfy guide constraints.
- [ ] Posterior predictive samples have expected site keys and leading sample dimensions.
- [ ] Optional dependencies (`optax`, `funsor`, plotting/data packages) are installed only when the chosen workflow needs them.
