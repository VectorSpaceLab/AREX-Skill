# SVI and autoguide troubleshooting

## Loss is NaN or infinite

**Symptoms**

- `losses` contains `nan`/`inf`.
- Parameters become non-finite after a few updates.

**Likely cause**

Invalid distribution support, unconstrained guide parameters used as positive/simplex values, too-large learning rate, impossible observations, or unstable model geometry.

**Fix**

1. Validate model distributions in `../distributions-transforms/`.
2. Trace model and guide on tiny data in `../modeling-primitives/`.
3. Add constraints to `numpyro.param`, e.g. `constraint=constraints.positive`.
4. Lower the learning rate or use `ClippedAdam`.
5. Try `svi.run(..., stable_update=True)` to skip non-finite updates while debugging.
6. Change initialization with `init_to_feasible`/`init_to_median` for autoguides.

## Guide missing or extra latent sites

**Symptoms**

- Warnings or wrong results because a model latent is not represented in the guide.
- `obs_mask` creates unexpected `*_unobserved` latent sites.

**Fix**

- Trace both model and guide on the same tiny arguments and compare latent sample-site names.
- Add guide sample sites for continuous model latents, or use an autoguide.
- If using `obs_mask`, include the generated `name + "_unobserved"` site in the guide or change the missing-data strategy.
- Use `AutoGuideList` plus `handlers.block` only when every latent is owned exactly once.

## Wrong ELBO for discrete latent variables

**Symptoms**

- Warning that SVI with the chosen loss does not support models with discrete latent variables.
- Enumeration shapes or indexes fail.

**Fix**

- Use `TraceEnum_ELBO` with `infer={"enumerate": "parallel"}` or `config_enumerate` when finite enumeration is intended.
- Install/verify `funsor` when enumeration is required.
- Use `Vindex` for indexing by enumerated values.
- Use `TraceGraph_ELBO` for score-function-style handling of discrete sites when enumeration is not used.
- Route discrete Gibbs sampling to `../mcmc-diagnostics/`.

## Missing Optax

**Symptoms**

- Import error says an optimizer is not a NumPyro optimizer and Optax must be installed.

**Likely cause**

An Optax `GradientTransformation` was passed to `SVI`, but `optax` is not installed.

**Fix**

- Use `numpyro.optim.Adam`, `ClippedAdam`, etc. if Optax is not needed.
- If Optax-specific transforms are required, install/verify `optax` and rerun a tiny SVI smoke.

## Autoguide initialization fails

**Symptoms**

- First SVI loss is non-finite.
- Autoguide cannot initialize a constrained latent site.

**Fix**

- Use `init_to_feasible()` or `init_to_median()` as `init_loc_fn`.
- Check observed data is inside likelihood support.
- Use stronger priors or explicit initial values for hard constrained sites.
- For high-dimensional correlated latents, start with `AutoDiagonalNormal` or `AutoNormal` before trying flow/DAIS guides.

## Local latent and subsampling issues

**Symptoms**

- Guide does not handle per-observation local latents under minibatching.
- DAIS or semi-DAIS reports admissibility errors.

**Fix**

- Use `plate(..., subsample_size=...)` and `numpyro.subsample` consistently.
- Verify local/global latent ownership in traces.
- Consider `AutoSemiDAIS` or a custom amortized guide only after a small manual-guide or AutoNormal baseline works.
- Keep tiny synthetic cases before scaling to full data.

## Posterior predictive from SVI has wrong shape

**Symptoms**

- `Predictive(model, guide=guide, params=params, num_samples=...)` output has unexpected leading dimensions.
- Deterministic sites are missing.

**Fix**

- Remember the leading dimension is `num_samples` from guide sampling.
- Pass `return_sites` to limit output.
- Set `exclude_deterministic=False` when deterministic sites are required.
- Trace the model with `data=None` and expected prediction arguments.
