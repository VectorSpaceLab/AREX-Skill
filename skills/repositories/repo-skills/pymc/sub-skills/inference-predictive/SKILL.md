---
name: inference-predictive
description: "Run, configure, validate, and troubleshoot PyMC inference and
  predictive workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# PyMC inference and predictive workflows

Use this sub-skill when the task is to run or debug PyMC posterior inference, NUTS/MCMC configuration, explicit step methods, external NUTS backends, prior or posterior predictive sampling, `pm.draw`, SMC, diagnostics, or trace/output backends.

## Runtime map

- Read [references/inference-workflows.md](references/inference-workflows.md) for MCMC/NUTS, explicit step methods, external NUTS, prior/posterior predictive sampling, `pm.draw`, SMC, and diagnostics.
- Read [references/api-reference.md](references/api-reference.md) for PyMC 6.3.0 signatures, parameter names, sampler kwargs, and output expectations.
- Read [references/backends-and-outputs.md](references/backends-and-outputs.md) for DataTree/ArviZ outputs, log-likelihood, Zarr, `mcbackend`, and legacy `MultiTrace` paths.
- Read [references/troubleshooting.md](references/troubleshooting.md) for sampling, predictive, external sampler, diagnostics, shape/coord, JAX, Zarr, or `mcbackend` failures.
- Run [scripts/inference_smoke.py](scripts/inference_smoke.py) to verify a local PyMC install with a tiny CPU model and output-group checks.

## Default stance

1. Prefer default `return_inferencedata=True` and work with DataTree groups such as `posterior`, `sample_stats`, `posterior_predictive`, `predictions`, and `log_likelihood`.
2. For reproducible local smokes, callbacks, custom traces, or mixed discrete/continuous models, pin `nuts_sampler="pymc"`.
3. With `nuts_sampler=None`, current PyMC may auto-select `nutpie` if installed and compatible. Pin the sampler explicitly when backend choice matters.
4. External NUTS (`nutpie`, `numpyro`, `blackjax`) is for all-continuous differentiable models and does not support custom `trace`, per-draw `callback`, or `return_inferencedata=False`.
5. Use `pm.sample_prior_predictive(draws=...)`, not older `samples=...`.
6. Validate real inference with divergences, tree depth, ESS, R-hat, sample size, and log-likelihood/model-comparison readiness.

Route model/data design to `../modeling-data/SKILL.md`, custom distributions/logp to `../distributions-logprob/SKILL.md`, and VI/ADVI/SVGD to `../advanced-workflows/SKILL.md`.
