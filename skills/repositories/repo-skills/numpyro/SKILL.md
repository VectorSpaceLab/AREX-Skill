---
name: numpyro
description: "Route NumPyro probabilistic programming tasks across modeling
  primitives, distributions, MCMC diagnostics, SVI/autoguides, JAX backends, and
  optional contrib workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# NumPyro repo skill

Use this repo skill when a task involves **NumPyro**, the JAX-backed probabilistic programming package: writing models with Pyro-like primitives, choosing distributions and transforms, running MCMC or SVI, diagnosing posterior geometry, configuring JAX CPU/GPU/TPU execution, or deciding whether an optional `numpyro.contrib` workflow is needed.

## First checks

- Package/import name: `numpyro`
- Supported Python from package metadata: Python `>=3.11`
- Minimal install:
  ```bash
  pip install numpyro
  ```
- CPU-pinned install when JAX compatibility is confusing:
  ```bash
  pip install 'numpyro[cpu]'
  ```
- CUDA installs are optional and must match JAX's current NVIDIA wheel guidance:
  ```bash
  pip install 'numpyro[cuda12]' -f https://storage.googleapis.com/jax-releases/jax_cuda_releases.html
  pip install 'numpyro[cuda13]' -f https://storage.googleapis.com/jax-releases/jax_cuda_releases.html
  ```
- Minimal import/backend check:
  ```python
  import jax
  import numpyro
  import numpyro.distributions as dist
  print(numpyro.__version__, jax.default_backend(), jax.devices())
  ```

For a stronger environment diagnostic, run [scripts/check_numpyro_environment.py](scripts/check_numpyro_environment.py). For a concise API/signature probe, run [scripts/api_quick_probe.py](scripts/api_quick_probe.py).

## Route by task

| User task or signal | Read |
|---|---|
| Write a model, inspect sample/param sites, condition/seed/trace, fix `plate` placement, use effect handlers, render or inspect model relations, handle JAX-compatible control flow. | [modeling-primitives](sub-skills/modeling-primitives/SKILL.md) |
| Choose or debug distributions, constraints, `batch_shape`/`event_shape`, `to_event`, `Independent`, `TransformedDistribution`, transforms, support validation, finite `log_prob`. | [distributions-transforms](sub-skills/distributions-transforms/SKILL.md) |
| Run NUTS/HMC/MCMC, choose kernels, collect extra fields, interpret divergences/ESS/`r_hat`, run posterior predictive or log likelihood, configure chains/devices/x64. | [mcmc-diagnostics](sub-skills/mcmc-diagnostics/SKILL.md) |
| Fit SVI, write a guide, choose ELBOs, use autoguides, debug guide parameters/losses, use discrete enumeration with SVI. | [svi-autoguides](sub-skills/svi-autoguides/SKILL.md) |
| Use optional contrib areas: Funsor enumeration helpers, HSGP, nested sampling, SteinVI/SVGD, Flax/NNX/Equinox module wrappers, TFP wrappers, stochastic-support inference. | [advanced-contrib](sub-skills/advanced-contrib/SKILL.md) |

## Shared references

- [Getting started](references/getting-started.md) explains the package mental model, install variants, minimal smoke checks, and common workflow sequence.
- [Cross-cutting troubleshooting](references/troubleshooting.md) covers install/import, JAX backend, optional dependencies, data downloads, dtype/precision, compilation, and source-versus-installed-package pitfalls.
- [Source artifact map](references/source-artifact-map.md) records which original docs/examples/scripts were distilled into bundled runtime references or helper scripts.
- [Repository provenance](references/repo-provenance.md) records the source version and evidence baseline for refresh decisions.
- [Router metadata](references/repo-routing-metadata.json) is consumed by the managed repo-skills-router importer.

## Operating guidance

1. Start with the sub-skill closest to the user's task. Do not open optional contrib guidance for ordinary core MCMC/SVI/distribution questions unless the task names a contrib API or optional dependency.
2. Validate a model in layers: distribution object checks, model trace/plate checks, then inference smoke. This prevents blaming MCMC/SVI for support or shape errors.
3. Treat GPU/TPU as optional acceleration unless the user explicitly requires accelerator verification. A CPU run verifies NumPyro semantics but not CUDA/TPU wheel compatibility.
4. Keep examples tiny while diagnosing. NumPyro/JAX first-run compilation can dominate small runs; distinguish compile latency from sampling/optimization failure.
5. Do not make runtime work depend on the original repository checkout. Use the bundled references and scripts in this skill tree, plus an installed NumPyro package.

## Common bundled scripts

- `python scripts/check_numpyro_environment.py --pretty` checks core imports, JAX backend, and selected optional dependencies without requiring the source repo.
- `python scripts/api_quick_probe.py --pretty` prints key public signatures for primitives, inference classes, autoguides, and utilities.
- Sub-skill scripts provide focused smokes for tracing, distributions/transforms, MCMC, SVI, and optional dependency probing.
