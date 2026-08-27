# Prediction Workflows

This reference covers Pyro predictive utilities in the 1.9.1-family API. Use it
after deciding which sites should be conditioned from posterior samples, sampled
from the prior, or explicitly returned to the caller.

## Core API Facts

| Object | Runtime signature pattern | Use |
|---|---|---|
| `Predictive(model, posterior_samples=None, guide=None, num_samples=None, return_sites=(), parallel=False)` | Construct a callable `torch.nn.Module`; call it as `predictive(*model_args, **model_kwargs)`. | Prior predictive, posterior predictive from MCMC samples, or guide-based predictive after SVI. |
| `WeighedPredictive(model, posterior_samples=None, guide=None, num_samples=None, return_sites=(), parallel=False)` | Same initialization pattern as `Predictive`; call can additionally pass `model_guide=conditioned_model`. | Draw guide-based predictive samples and return log weights for importance-weighted summaries. |
| `MHResampler(sampler, source_samples_slice=slice(0), stored_samples_slice=slice(0))` | Wraps a callable that returns `WeighedPredictiveResults`; repeated calls perform MH resampling. | Convert weighted predictive samples toward equally weighted samples. |
| `predictive.get_vectorized_trace(*args, **kwargs)` | Requires a model with correctly annotated plates. | Inspect a single vectorized trace for returned values or debugging. |
| `predictive.get_samples(...)` | Deprecated alias for `forward()` on `Predictive`-style objects. | Prefer calling the object directly in new code. |

`Predictive` masks model and guide log-probability terms during forward sampling;
it is for simulation/inspection, not for computing training losses.

## Prior Predictive Sampling

Use prior predictive sampling when there are no posterior samples yet, or when
checking whether priors imply plausible observations.

```python
from pyro.infer import Predictive


def model(features, y=None):
    weight = pyro.sample("weight", dist.Normal(0.0, 1.0))
    rate = pyro.deterministic("rate", (features * weight).exp())
    with pyro.plate("data", features.size(0), dim=-1):
        return pyro.sample("obs", dist.Poisson(rate), obs=y)

prior = Predictive(
    model,
    num_samples=100,
    return_sites=["weight", "rate", "obs", "_RETURN"],
    parallel=False,
)
prior_samples = prior(features, None)
```

Rules:

- If `posterior_samples` is empty or omitted, `num_samples` is required.
- Pass `None` for an observation argument when you want that observation site to
  be sampled instead of clamped.
- Use explicit `return_sites` when you care about deterministic sites,
  observations, or `_RETURN`.
- The leading dimension of returned tensors is the predictive sample dimension.

## Posterior Predictive From MCMC Samples

After MCMC:

```python
kernel = NUTS(model)
mcmc = MCMC(kernel, num_samples=500, warmup_steps=500, disable_progbar=True)
mcmc.run(train_x, train_y)
posterior_samples = mcmc.get_samples()

posterior_predictive = Predictive(
    model,
    posterior_samples=posterior_samples,
    return_sites=["obs", "rate"],
    parallel=False,
)
y_rep = posterior_predictive(train_x, None)
```

Rules:

- `posterior_samples` keys are conditioned latent sites. Do not include sites
  that should be resampled.
- If `num_samples` is also provided and disagrees with the leading dimension of a
  posterior sample, Pyro warns and uses the posterior sample batch size.
- Default `return_sites=()` returns sample/observation sites not present in
  `posterior_samples`. Explicit `return_sites=[...]` is clearer for observed and
  deterministic sites.
- `mcmc.get_samples(group_by_chain=True)` has a chain dimension; flatten or
  select samples before passing to `Predictive`, unless your model deliberately
  expects that extra leading dimension.

## Deterministic And Observed Sites

`pyro.deterministic(name, value, event_dim=...)` records a Delta-like sample site
that is useful in posterior predictive analysis. To inspect deterministic values,
request them explicitly:

```python
def model(x, y=None):
    coef = pyro.sample("coef", dist.Normal(0, 1).expand([x.size(-1)]).to_event(1))
    logits = pyro.deterministic("logits", x @ coef, event_dim=1)
    with pyro.plate("data", x.size(0), dim=-1):
        return pyro.sample("obs", dist.Bernoulli(logits=logits), obs=y)

pred = Predictive(model, posterior_samples, return_sites=["logits", "obs", "_RETURN"])
out = pred(x_new, None)
```

Shape notes:

- Returned shape is generally `(num_predictive_samples,) + site_batch_shape +
  site_event_shape`.
- Deterministic sites can include singleton dimensions introduced by plate and
  event semantics. Inspect `tuple(value.shape)` before squeezing.
- If an observed site still receives non-`None` `obs`, `Predictive` returns the
  observed value repeated/broadcast rather than drawing new observations.
- For models with all batch dimensions declared via `pyro.plate`,
  `parallel=True` can vectorize predictive sampling. If shape errors appear,
  fall back to `parallel=False` while repairing plate annotations.

## Guide-Based Predictive After SVI

When an SVI guide has been fitted, let `Predictive` draw latent samples from the
guide and then replay the model:

```python
# Fit the guide elsewhere via SVI.
predictive = Predictive(
    model,
    guide=guide,
    num_samples=500,
    return_sites=["latent", "obs"],
    parallel=False,
)
samples = predictive(*model_args_with_obs_none)
```

Rules:

- Do not pass both `posterior_samples` and `guide`; Pyro raises an error.
- If `guide` is provided and `return_sites` is left empty, Pyro returns all model
  sample/observation sites by default after drawing guide samples.
- The guide and model must accept compatible `*args, **kwargs`; guide fitting and
  autoguide selection are owned by `../svi-and-autoguides/`.
- `parallel=True` requires both guide and model to be valid under an outer
  predictive plate.

A common bridge from guide samples to posterior predictive is:

```python
posterior_samples = Predictive(guide, num_samples=1000)(*args)
posterior_predictive = Predictive(model, posterior_samples, return_sites=["obs"])
out = posterior_predictive(*model_args_with_obs_none)
```

## Weighted Predictive And MH Resampling

`WeighedPredictive` is Pyro's spelling for weighted predictive sampling. It is
useful when a fitted guide is not exactly the posterior and you want importance
weights:

```python
from pyro.infer import WeighedPredictive, MHResampler
from pyro.ops.stats import quantile, weighed_quantile

weighted_predictive = WeighedPredictive(
    model,
    guide=guide,
    num_samples=1000,
    return_sites=["_RETURN"],
    parallel=False,
)
weighted = weighted_predictive(*args, model_guide=conditioned_model)
values = weighted.samples["_RETURN"]
log_weights = weighted.log_weights
weighted_q95 = weighed_quantile(values, [0.95], log_weights)[0]

resampler = MHResampler(weighted_predictive)
for _ in range(10):
    resampled = resampler(*args, model_guide=conditioned_model)
resampled_q95 = quantile(resampled.samples["_RETURN"], [0.95])[0]
```

The call-time `model_guide` is the observed/conditioned model used when fitting
the guide. If omitted, `WeighedPredictive` uses `self.model`. Inspect
`weighted.get_ESS()` from the result mixin when deciding whether weighted
summaries are reliable.

## Predictive Debug Checklist

1. Decide whether the task is prior predictive, posterior predictive from MCMC,
   guide-based posterior predictive, or weighted predictive.
2. Make observation arguments optional (`y=None`) so predictive calls can sample
   observations.
3. Use explicit `return_sites` for deterministic sites, observed sites, and
   `_RETURN`.
4. Print `{name: tuple(value.shape) for name, value in samples.items()}` before
   writing downstream shape assumptions.
5. Keep `parallel=False` until the sequential predictive result is correct; then
   enable `parallel=True` only for plate-annotated static models.
6. Do not use predictive samples as evidence of MCMC/SVI convergence; inspect
   sampler or training diagnostics separately.
