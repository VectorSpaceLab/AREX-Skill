# Predictive sampling and log likelihood

Use this reference after a model has posterior samples from MCMC, guide samples from SVI, or explicit posterior parameter draws.

## Posterior predictive from MCMC samples

```python
from jax import random
from numpyro.infer import Predictive

posterior_samples = mcmc.get_samples()  # flattened leading sample dimension
predictive = Predictive(model, posterior_samples=posterior_samples)
posterior_predictive = predictive(random.key(1), *new_model_args, **new_model_kwargs)
```

Notes:

- `posterior_samples` is a dict keyed by latent site name.
- Flattened samples are usually appropriate for `Predictive`; use grouped samples only when you explicitly manage `batch_ndims`.
- `return_sites=(...)` restricts output. Include deterministic sites if needed.
- `exclude_deterministic=True` by default in the verified signature; set `exclude_deterministic=False` when deterministic values should be returned.

## Prior predictive

```python
prior_predictive = Predictive(model, num_samples=100)
prior_samples = prior_predictive(random.key(0), *args, **kwargs)
```

Use prior predictive checks before inference to catch impossible scales, support errors, or shape mismatches.

## Predictive with a guide or SVI params

For SVI results, route fitting and guide choice to `../svi-autoguides/`, then use:

```python
predictive = Predictive(model, guide=guide, params=svi_result.params, num_samples=500)
y_rep = predictive(random.key(2), data=None)
```

To inspect posterior guide samples directly:

```python
guide_predictive = Predictive(guide, params=svi_result.params, num_samples=500)
posterior_latents = guide_predictive(random.key(3), data=None)
```

## Pointwise log likelihood

```python
from numpyro.infer import log_likelihood

posterior_samples = mcmc.get_samples()
ll = log_likelihood(model, posterior_samples, *model_args, **model_kwargs)
obs_ll = ll["obs"]
```

Typical shape is `(num_posterior_samples, *observation_batch_shape)` for each observed site. Use it for WAIC/LOO-style workflows or expected log predictive density. If a model has multiple observed sites, `log_likelihood` returns one array per site.

## Extra fields and expected log joint

If `potential_energy` was collected:

```python
energy = mcmc.get_extra_fields()["potential_energy"]
expected_log_joint = -energy.mean()
```

This is not the same as pointwise log likelihood; it includes prior and transformed latent terms. Use it for energy diagnostics or coarse run comparisons, not as a data-point scoring array.

## Batch dimensions and `batch_ndims`

- `Predictive` and `log_likelihood` assume leading dimensions of posterior samples are sample dimensions.
- Default `batch_ndims=1` is right for flattened `mcmc.get_samples()` output.
- If samples are grouped by chain with shape `(num_chains, num_samples, ...)`, set `batch_ndims=2` or flatten before calling.

```python
grouped = mcmc.get_samples(group_by_chain=True)
ll_grouped = log_likelihood(model, grouped, *args, batch_ndims=2, **kwargs)
```

## Common pitfalls

| Symptom | Likely cause | Fix |
|---|---|---|
| Predictive output is missing deterministic sites. | Default `exclude_deterministic=True`. | Set `exclude_deterministic=False` or list `return_sites`. |
| Predictive shape has unexpected chain/sample dims. | Grouped posterior samples used with wrong `batch_ndims`. | Flatten samples or set `batch_ndims=2`. |
| `log_likelihood` fails on held-out data. | Model args/kwargs changed shape or missing observed site input. | Re-run a trace with held-out data and check observation shapes. |
| Output includes latent sites you did not need. | `return_sites` omitted. | Pass `return_sites=("obs", ...)` or deterministic site names. |
| Memory blow-up on large posterior predictive. | Too many posterior samples or large observation batch. | Thin/subsample posterior samples or batch predictions manually. |
