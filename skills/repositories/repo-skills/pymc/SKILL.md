---
name: pymc
description: "Use PyMC for Bayesian probabilistic programming, model
  construction, distributions, MCMC/NUTS inference, predictive checks,
  diagnostics, and advanced GP/ODE/VI workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# PyMC repo skill

Use this skill when a task needs PyMC-specific operating knowledge: Bayesian model graphs, coordinates and dimensions, `pm.Data`, distribution/log-probability design, `CustomDist`, MCMC/NUTS, prior or posterior predictive sampling, DataTree/ArviZ outputs, diagnostics, Gaussian processes, ODE likelihoods, or variational inference.

## Start here

- Read [references/repo-provenance.md](references/repo-provenance.md) before relying on this skill for a different PyMC checkout or when deciding whether to refresh it.
- Read [references/installation-and-environment.md](references/installation-and-environment.md) when installing PyMC, checking optional samplers, or choosing `nutpie`, JAX/NumPyro/BlackJAX, Zarr, `mcbackend`, Graphviz, or CPU/GPU routes.
- Read [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting install/import, PyTensor compiler, optional backend, DataTree/ArviZ, and Graphviz failures.
- Run [scripts/check_pymc_env.py](scripts/check_pymc_env.py) to check PyMC importability, versions, optional modules, and an optional tiny model smoke.
- Run [scripts/pymc_quick_smoke.py](scripts/pymc_quick_smoke.py) for a tiny end-to-end CPU model, `pm.sample`, predictions, and `pm.do` intervention check.

Minimal public install and import check:

```bash
python -m pip install pymc
python -c "import pymc as pm; print(pm.__version__)"
```

For faster optional NUTS support, install `pymc[nutpie]`. Install `numpyro`, `blackjax`, and JAX packages only when a task actually needs JAX-backed samplers.

## Route by task

| If the user asks about... | Use |
| --- | --- |
| Building a model with `with pm.Model`, named variables, observed data, missing values, `coords`/`dims`, `pm.Data`, `pm.set_data`, `Deterministic`, `Potential`, `compile_logp`, model debugging, graph visualization, `pm.do`, or `pm.observe` | [sub-skills/modeling-data/SKILL.md](sub-skills/modeling-data/SKILL.md) |
| Choosing distributions, `.dist()` components, shapes/support dimensions, transforms, `CustomDist`, `DensityDist`, mixtures, truncation/censoring, or `pm.logp`/`pm.logcdf` | [sub-skills/distributions-logprob/SKILL.md](sub-skills/distributions-logprob/SKILL.md) |
| Running `pm.sample`, NUTS/MCMC, step methods, external samplers (`nutpie`, `numpyro`, `blackjax`), prior/posterior predictive sampling, `pm.draw`, SMC, diagnostics, log-likelihood, DataTree/ArviZ outputs, Zarr, or `mcbackend` | [sub-skills/inference-predictive/SKILL.md](sub-skills/inference-predictive/SKILL.md) |
| Gaussian processes, `pm.ode.DifferentialEquation`, ADVI/FullRankADVI/SVGD/ASVGD, `pm.fit`, approximation sampling, minibatches, or advanced `pymc.dims` interactions | [sub-skills/advanced-workflows/SKILL.md](sub-skills/advanced-workflows/SKILL.md) |

## Operating defaults

1. Build models in a `with pm.Model(coords=...) as model:` context. Use `pm.Data` only for values you intend to replace later.
2. Use regular `coords`/`dims` for stable output labels and shape metadata. Treat `pymc.dims` as experimental and read the modeling/advanced sub-skill before using it.
3. Use `.dist()` for unregistered component distributions in mixtures, truncation, censoring, and symbolic custom distributions.
4. For deterministic smokes, pin `nuts_sampler="pymc"`, `chains=1`, `cores=1`, tiny draws/tune, and `compute_convergence_checks=False`. Do not treat tiny-draw smokes as statistical convergence evidence.
5. For real inference, increase `draws`, `tune`, and `chains`; inspect divergences, tree depth, ESS, R-hat, and log-likelihood/model-comparison readiness.
6. Prefer default DataTree outputs (`return_inferencedata=True`). Use `pm.compute_log_likelihood` when model comparison needs a `log_likelihood` group.
7. When changing data length for prediction, update both `pm.Data` values and matching `coords`, then use posterior predictive guidance from `inference-predictive`.

## Common task chains

- **Out-of-sample predictions with changed covariates:** read `modeling-data` for `pm.Data`/coords mutation, then `inference-predictive` for `sample_posterior_predictive(predictions=True)` and output validation.
- **Custom likelihood or mixture model:** read `distributions-logprob` for `.dist()`, support, signature, and logp checks; then `inference-predictive` for sampling and diagnostics.
- **Scientific GP or ODE model:** read `advanced-workflows` for GP/ODE construction; then `modeling-data` for shared coordinates/data and `inference-predictive` for posterior/predictive execution.
- **Approximate large-data workflow:** read `advanced-workflows` for VI/minibatches, then use `inference-predictive` only for final posterior predictive and diagnostic output handling.

## Self-contained runtime helpers

These helpers are safe, tiny, and CPU-first:

```bash
python scripts/check_pymc_env.py --run-smoke --json
python scripts/pymc_quick_smoke.py --draws 10 --tune 10 --json
python sub-skills/modeling-data/scripts/model_data_smoke.py --posterior-predictive --draws 5 --tune 5 --quiet
python sub-skills/distributions-logprob/scripts/distribution_logp_smoke.py --json
python sub-skills/inference-predictive/scripts/inference_smoke.py --draws 5 --tune 5 --json
python sub-skills/advanced-workflows/scripts/advanced_workflows_smoke.py --all --vi-iterations 3 --vi-draws 3 --json
```

Do not link future work to PyMC source docs, notebooks, tests, or scripts as runtime dependencies. Use this skill's bundled references and scripts, and refresh the skill if a newer checkout changes public APIs or optional backend behavior.
