# Variational inference API reference

This reference collects the exact objective and flow entry points for ZhuSuan's
variational workflows.

## Core objectives

```python
elbo(meta_bn, observed, latent=None, axis=None, variational=None)
importance_weighted_objective(meta_bn, observed, latent=None, axis=None,
                               variational=None)
klpq(meta_bn, observed, latent=None, axis=None, variational=None)
is_loglikelihood(meta_bn, observed, latent=None, axis=None, proposal=None)
AIS(meta_bn, proposal_meta_bn, hmc, observed, latent,
    n_temperatures=1000, n_adapt=30, verbose=False)
```

## Objective methods

```python
lower_bound.sgvb()
lower_bound.reinforce(variance_reduction=True, baseline=None, decay=0.8)
objective.vimco()
objective.importance()
```

## Flow helpers

```python
linear_ar(name, id, z, hidden=None)
planar_normalizing_flow(samples, log_probs, n_iters)
inv_autoregressive_flow(samples, hidden, log_probs, autoregressive_nn,
                        n_iters, update='normal')
```

## Practical notes

- Use `variational=` instead of the deprecated `latent=` argument.
- Multi-sample objectives need a correct `axis` that identifies the sample
  dimension.
- `vimco()` requires more than one sample along the chosen axis.
- Flow helpers expect the sample tensor and log-probability tensor to stay
  aligned on every axis except the transformed sample axis.
