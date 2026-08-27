---
name: advanced-contrib
description: "Route and use optional NumPyro contrib workflows while keeping
  dependency and core-API boundaries explicit."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# advanced-contrib

Use this sub-skill when a NumPyro task explicitly involves optional or experimental `numpyro.contrib.*` workflows rather than always-installed core modeling, distributions, MCMC, or SVI.

## Triggers

Load this sub-skill for requests involving:

- `numpyro.contrib.funsor` enumeration helpers: `config_enumerate`, `infer_discrete`, `markov`, enum handlers, or exact marginalization of discrete latent variables.
- Hilbert-space Gaussian process approximations in `numpyro.contrib.hsgp`.
- `numpyro.contrib.nested_sampling.NestedSampler` and nested sampling through `jaxns`.
- `numpyro.contrib.einstein` particle/Stein inference: `SteinVI`, `SVGD`, `ASVGD`, Stein kernels, or `MixtureGuidePredictive`.
- `numpyro.contrib.module` wrappers for Flax Linen, Flax NNX, or Equinox modules.
- TensorFlow Probability integration through `numpyro.contrib.tfp` or direct TFP JAX substrate distributions in NumPyro models.
- Stochastic-support inference: `DCC`, `SDVI`, or branch sites marked with `infer={"branching": True}`.

## First routing decision

1. If the request is plain `sample`, `param`, `plate`, handlers, `module`, `mutable`, `scan`, or `cond`, route to [modeling-primitives](../modeling-primitives/SKILL.md).
2. If it is native `numpyro.distributions`, constraints, transforms, support, shapes, or TFP distribution fallback selection, route to [distributions-transforms](../distributions-transforms/SKILL.md) and return here only for TFP-specific caveats.
3. If it is ordinary `MCMC`, `NUTS`, `HMC`, diagnostics, chain methods, or discrete HMC Gibbs, route to [mcmc-diagnostics](../mcmc-diagnostics/SKILL.md) and return here only for `NestedSampler` or TFP MCMC kernels.
4. If it is ordinary `SVI`, ELBO choice, autoguides, optimizers, or predictive use, route to [svi-autoguides](../svi-autoguides/SKILL.md) and return here only for SteinVI/SVGD/ASVGD or `SDVI`.
5. If the task names `contrib`, an optional dependency, or one of the APIs above, stay in this sub-skill and check optional dependencies before coding.

## Required workflow

- Treat contrib features as optional. A missing optional dependency is not evidence that core NumPyro is broken.
- Before suggesting or executing contrib code in a minimal environment, run or adapt `scripts/check_optional_dependencies.py`:
  - `python scripts/check_optional_dependencies.py --pretty`
  - `python scripts/check_optional_dependencies.py --require nested_sampling`
  - `python scripts/check_optional_dependencies.py --require module_flax`
- Keep examples bounded: tiny synthetic data, CPU-safe sample counts, no downloads, no plotting unless the task explicitly asks for plots and plotting dependencies are present.
- Prefer native NumPyro APIs for core tasks; use contrib only when it adds a capability not covered by the sibling sub-skills.

## Reference map

- [Contrib overview and routing](references/advanced-contrib.md)
- [Optional dependency matrix](references/optional-dependencies.md)
- [HSGP, TFP, and nested sampling](references/hsgp-and-tfp.md)
- [Troubleshooting optional workflows](references/troubleshooting.md)
