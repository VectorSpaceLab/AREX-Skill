---
name: distributions-transforms
description: "Choose, instantiate, validate, sample, score, transform, compose,
  and debug NumPyro distributions, constraints, transforms, and shape
  semantics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# NumPyro distributions and transforms

Use this sub-skill when the task is about **distribution objects** rather than full NumPyro model execution: choosing a distribution, constructing it with valid parameters, sampling and scoring values, interpreting `batch_shape`/`event_shape`, validating support, masking/expanding distributions, composing bijective transforms, or debugging finite `log_prob` issues.

## Triggers

- Choose between common continuous, discrete, mixture, `Delta`, zero-inflated, or transformed distributions.
- Explain or fix `sample_shape + batch_shape + event_shape` behavior.
- Decide whether to use `expand`, `mask`, `to_event`, or `Independent` for a distribution object.
- Validate parameters and values with constraints, `biject_to`, `enable_validation`, or `validation_enabled`.
- Compose transforms such as `AffineTransform`, `ComposeTransform`, `StickBreakingTransform`, `LowerCholeskyTransform`, `HaarTransform`, or `DiscreteCosineTransform`.
- Check transform round-trips, shape-changing bijectors, or finite transformed-distribution log densities.

## Quick workflow

1. **Classify the request.** Distribution-only work stays here. If the user asks about `numpyro.sample`, `plate`, handlers, or model traces, route to `../modeling-primitives/`. If they ask to run MCMC/SVI, route to `../mcmc-diagnostics/` or `../svi-autoguides/`.
2. **Pick the distribution family.** Use [references/distribution-api.md](references/distribution-api.md) for constructors, common methods, mixtures, zero-inflation, `Delta`, `TransformedDistribution`, `Independent`, `expand`, and `mask`.
3. **Check shapes before sampling.** Confirm expected `sample_shape`, `batch_shape`, `event_shape`, and resulting `log_prob` shape using [references/shape-and-support.md](references/shape-and-support.md).
4. **Validate support.** Use distribution `support`, `constraints`, constructor `validate_args=True`, and `validation_enabled(True)` while debugging outside JIT/vmap.
5. **Choose transforms by target support.** Prefer `biject_to(constraint)` for constrained latent variables, then run a round-trip/log-det check from [references/transform-workflows.md](references/transform-workflows.md).
6. **Run the bundled smoke when unsure.** Execute [scripts/distribution_transform_smoke.py](scripts/distribution_transform_smoke.py) in an environment where NumPyro and JAX are installed.
7. **Triage symptoms.** For invalid values, shape mismatches, NaN/inf log densities, domain/codomain errors, or dtype/x64 issues, use [references/troubleshooting.md](references/troubleshooting.md).

## Routing and exclusions

- **Model/sample-site semantics:** use `../modeling-primitives/` for `numpyro.sample`, `plate`, `handlers.mask`, `handlers.reparam`, `format_shapes`, and model inspection.
- **MCMC and diagnostics:** use `../mcmc-diagnostics/` for `MCMC`, `NUTS`, `HMC`, divergences, predictive sampling, and log likelihood workflows.
- **SVI/autoguides:** use `../svi-autoguides/` for `SVI`, ELBOs, guide parameters, autoguides, and enumeration choices.
- **TFP wrappers and optional contrib distributions:** use `../advanced-contrib/`; return here only for core NumPyro distribution shape/support/transform mechanics.
- **Do not run expensive inference here.** Use only deterministic CPU-safe sampling/scoring/transform checks.

## Bundled materials

- [Distribution API reference](references/distribution-api.md)
- [Shape and support guide](references/shape-and-support.md)
- [Transform workflows](references/transform-workflows.md)
- [Troubleshooting matrix](references/troubleshooting.md)
- [Distribution/transform smoke script](scripts/distribution_transform_smoke.py)
