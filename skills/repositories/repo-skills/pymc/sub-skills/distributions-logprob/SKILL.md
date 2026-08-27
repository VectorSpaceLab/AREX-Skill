---
name: distributions-logprob
description: "Choose, parameterize, shape, extend, and validate PyMC
  distributions and log-probability graphs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# PyMC distributions and log-probability graphs

Use this sub-skill when the task is to choose a PyMC probability distribution, parameterize it, reason about `shape`/`size`/`dims` and support dimensions, build unregistered component distributions with `.dist()`, define a `CustomDist`/`DensityDist`, or inspect `pm.logp` / `pm.logcdf` graphs.

## Operating checklist

1. Decide whether the variable should be registered (`pm.Normal("x", ...)`) or an unregistered component (`pm.Normal.dist(...)`). Components for mixtures, truncation, censoring, and symbolic custom graphs should almost always use `.dist()`.
2. Choose the family by support and dependency structure: continuous, discrete, multivariate, time-series, mixture/zero-inflated/hurdle, censored/truncated, simulator, or custom.
3. Set `shape`/`size`/`dims` deliberately. `dims` belongs to registered model variables; `.dist(dims=...)` is not supported.
4. Validate support, parameter domains, broadcasting, transforms, and initial values before spending time on inference.
5. For custom distributions, provide consistent `logp`, optional `random`, optional `logcdf`, optional `support_point`, and `signature`/`ndims_params` when support or parameter dimensions are not scalar.

## Bundled resources

- Read [references/distribution-workflows.md](references/distribution-workflows.md) for choosing distribution families, `.dist()`, shapes/dims/support dimensions, and custom distributions.
- Read [references/api-reference.md](references/api-reference.md) for verified signatures and parameter notes.
- Read [references/troubleshooting.md](references/troubleshooting.md) for mixture, custom logp, transform, support point, or broadcasting errors.
- Run [scripts/distribution_logp_smoke.py](scripts/distribution_logp_smoke.py) for a tiny safe smoke of `CustomDist`, mixture `.dist()` components, `pm.logp`, and shape output.

## Route elsewhere

- General model context/data mutation: `../modeling-data/SKILL.md`.
- Sampling and posterior predictive execution: `../inference-predictive/SKILL.md`.
- Gaussian-process modeling family details: `../advanced-workflows/SKILL.md`.
