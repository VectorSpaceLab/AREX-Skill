# MCMC and sampling API reference

This reference collects the exact sampler and diagnostics entry points for
ZhuSuan's posterior-sampling workflows.

## Samplers

```python
HMC(step_size=1.0, n_leapfrogs=10, adapt_step_size=None,
    target_acceptance_rate=0.8, gamma=0.05, t0=100, kappa=0.75,
    adapt_mass=None, mass_collect_iters=10, mass_decay=0.99)
HMC.sample(meta_bn, observed, latent)

SGLD(learning_rate)
PSGLD(learning_rate, preconditioner='rms', preconditioner_hparams=None)
SGHMC(learning_rate, friction=0.25, variance_estimate=0.0,
      n_iter_resample_v=20, second_order=True)
SGNHT(learning_rate, variance_extra=0.0, tune_rate=1.0,
      n_iter_resample_v=None, second_order=True, use_vector_alpha=True)
```

## AIS and diagnostics

```python
AIS(meta_bn, proposal_meta_bn, hmc, observed, latent,
    n_temperatures=1000, n_adapt=30, verbose=False)
effective_sample_size_1d(samples)
effective_sample_size(samples, burn_in=100)
```

## Practical notes

- `HMC.sample(...)` is intended to be called once per sampler instance.
- Adaptation knobs should usually be active only during burn-in.
- `effective_sample_size` expects a 2-D array; flatten multi-dimensional
  chains first when you want a scalar summary.
