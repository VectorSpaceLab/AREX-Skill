# MCMC troubleshooting

## Not enough devices for parallel chains

**Symptoms**

- Warning: not enough devices to run parallel chains; chains drawn sequentially.
- `num_chains > 1` but only one CPU device appears.

**Fix**

Call `numpyro.set_host_device_count(num_chains)` before JAX initializes, or run with `XLA_FLAGS=--xla_force_host_platform_device_count=<n>`. Alternatively set `chain_method="sequential"` or `"vectorized"` explicitly.

## GPU is visible but NumPyro/JAX runs on CPU

**Symptoms**

- JAX warns that an NVIDIA GPU may be present but CUDA `jaxlib` is not installed.
- `jax.default_backend()` reports `cpu`.

**Fix**

Install the documented CUDA JAX/NumPyro extra that matches the driver/CUDA generation, then verify `jax.devices()` and a tiny device operation. If accelerator execution is optional, force CPU and state that GPU was not verified.

## Invalid initial parameters

**Symptoms**

- Initialization fails before sampling.
- Potential energy is non-finite at the initial state.

**Likely cause**

Distribution support violation, impossible observed values, bad parameterization, or too-diffuse priors.

**Fix**

1. Trace the model with tiny data in `../modeling-primitives/`.
2. Validate every site distribution in `../distributions-transforms/`.
3. Try `init_to_feasible()`, `init_to_median()`, or `init_to_value(values={...})`.
4. Add validation and stronger priors if the model can generate impossible values.

## Divergences or poor `r_hat`/ESS

**Symptoms**

- `Number of divergences` is nonzero.
- `r_hat` noticeably exceeds 1.
- ESS is much lower than raw sample count.

**Fix**

- Increase warmup and sample count after plumbing is correct.
- Raise `target_accept_prob` to 0.9 or 0.95.
- Reparameterize funnels and hierarchical scale sites using non-centered forms, `LocScaleReparam`, or `TransformReparam`.
- Consider `dense_mass=True` or dense blocks for correlated sites.
- Enable x64 if numerical precision is suspect.
- Reassess the model/prior if diagnostics remain poor.

## Discrete latent variable errors

**Symptoms**

- NUTS/HMC complains about discrete latent sites.
- Enumerated site shapes are wrong.

**Fix**

- For finite support and tractable enumeration, annotate sites with `infer={"enumerate": "parallel"}`.
- Use `DiscreteHMCGibbs` or `MixedHMC` when sampling discrete sites is intended.
- Use `TraceEnum_ELBO` and Funsor routes in `../svi-autoguides/`/`../advanced-contrib/` for variational enumeration.
- Use `Vindex`-style indexing when indexing tensors by enumerated discrete values.

## Long compile times or memory pressure

**Symptoms**

- First run is slow; later runs are faster.
- GPU/CPU memory spikes during compilation or sampling.

**Fix**

- Distinguish first-run JAX compilation from sampling time.
- Use smaller synthetic data to validate model plumbing.
- Set `progress_bar=False` for very small or heavily vectorized runs.
- Use `jit_model_args=True` for repeated same-shaped datasets.
- Transfer states to host after large runs.
- Reduce `num_chains`, sample count, dense mass blocks, or posterior predictive batch size.

## HMCECS/subsampling pitfalls

**Symptoms**

- HMCECS cannot detect a subsample plate.
- Subsampled likelihood produces biased or unstable results.

**Fix**

- Use `numpyro.plate("N", n, subsample_size=...)` and `numpyro.subsample` inside the plate.
- Train/reference parameters for `HMCECS.taylor_proxy` carefully; route SVI prefit issues to `../svi-autoguides/`.
- Validate on a tiny mock dataset before using large downloaded datasets.

## Posterior predictive shape surprises

**Symptoms**

- Predictive output has an unexpected leading dimension.
- Log likelihood arrays do not match observation count.

**Fix**

- Use flattened `mcmc.get_samples()` with default `batch_ndims=1`, or grouped samples with `batch_ndims=2`.
- Restrict `return_sites` and set `exclude_deterministic=False` when deterministic values are needed.
- Trace the model with the prediction data to check observation shapes.
