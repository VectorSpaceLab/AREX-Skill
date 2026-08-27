# MCMC troubleshooting

## HMC-specific

- `HMC.sample(...)` is intended to be called once per `HMC` instance.
- `adapt_step_size` and `adapt_mass` are usually placeholders so burn-in can be
  separated from sampling.
- `adapt_mass` requires `adapt_step_size`.
- If acceptance rates collapse, shrink the step size or lower the number of
  leapfrog steps.

## SG-MCMC-specific

- `SGHMC` needs `variance_estimate < friction`.
- `SGNHT` can use either scalar or vector friction. Choose `use_vector_alpha`
  only when you need per-component adaptation.
- `n_iter_resample_v` controls how often the momentum is resampled.

## AIS-specific

- AIS needs a proposal model, a target model, and an `HMC` instance.
- If the temperature schedule behaves oddly, check the proposal initialization
  and the number of adaptation iterations.
- The latent state must be represented by `Variable` objects so AIS can update
  them in place.

## Diagnostics / shapes

- `effective_sample_size` expects a 2-D array of shape `(M, D)`.
- Flatten multi-dimensional latents before passing them to the diagnostic if
  you want a scalar ESS summary.
- If the `log_joint` output shape is wrong, the sampler usually fails before
  the first update. The log joint must match the chain axes.

## Example/data issues

- PMF and topic-model examples depend on external data files and can be slow.
- If you only need a sanity check, run the bundled smoke script instead of the
  full example loops.
