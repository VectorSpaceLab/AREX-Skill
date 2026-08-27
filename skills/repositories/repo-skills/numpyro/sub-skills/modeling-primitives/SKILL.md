---
name: modeling-primitives
description: "Write and inspect NumPyro model programs with primitives, plates,
  handlers, JAX PRNG keys, control flow, and model tracing utilities."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# modeling-primitives

Use this sub-skill when the task is to write, inspect, or debug a NumPyro **model program** before choosing an inference algorithm: `sample`/`param` sites, `plate` shapes, effect handlers, JAX PRNG keys, conditioning, masking, reparameterization handlers, model traces, control flow, and model rendering.

## Quick workflow

1. **Write a pure JAX-compatible model.** Use [references/modeling-primitives.md](references/modeling-primitives.md) for `numpyro.sample`, `param`, `plate`, `deterministic`, `factor`, PRNG behavior, and functional-style constraints.
2. **Separate distribution shape from model-site shape.** First validate the distribution object with [../distributions-transforms/](../distributions-transforms/), then place observation axes in `plate` here.
3. **Use handlers for alternate interpretations.** Use [references/effect-handlers.md](references/effect-handlers.md) for `seed`, `trace`, `condition`, `substitute`, `replay`, `block`, `mask`, `scale`, `reparam`, `do`, and `scope`.
4. **Inspect before inference.** Use [references/model-inspection.md](references/model-inspection.md) to trace a model, check site metadata, render a dependency graph when `graphviz` is installed, or summarize shapes.
5. **Use JAX control flow for dynamic programs.** Prefer `numpyro.contrib.control_flow.scan` and `cond` when Python loops or branches interact with JIT, vectorization, or time-series latent structure.
6. **Run the smoke script.** [scripts/model_trace_smoke.py](scripts/model_trace_smoke.py) checks deterministic seeding, conditioning, and trace metadata without MCMC/SVI.
7. **Triage symptoms.** Use [references/troubleshooting.md](references/troubleshooting.md) for missing RNG keys, duplicate site names, plate collisions, tracer errors, masked observation confusion, and observed/conditioned site mistakes.

## Route elsewhere when

- The task is choosing or fixing a distribution constructor, support constraint, transform, or `log_prob` shape: use [../distributions-transforms/](../distributions-transforms/).
- The task is running NUTS/HMC or interpreting divergences, ESS, `r_hat`, or posterior predictive output from MCMC: use [../mcmc-diagnostics/](../mcmc-diagnostics/).
- The task is fitting a guide, choosing an ELBO, using autoguides, or handling SVI losses: use [../svi-autoguides/](../svi-autoguides/).
- The task depends on optional contrib modules such as Flax/Equinox wrappers, Funsor, TFP, nested sampling, HSGP, or SteinVI: use [../advanced-contrib/](../advanced-contrib/).

## Common trigger phrases

- "Trace this model", "condition observations", "seed a model", "why does sample need a key?"
- "Fix plate shape", "use subsampling", "mask observations", "make this model JAX-compatible"
- "Render a model graph", "inspect model relations", "convert a loop to scan"
- "Use reparam handler", "hide a site", "substitute parameter values"

## Bundled materials

- [Modeling primitives](references/modeling-primitives.md) explains model-site APIs and JAX/PRNG rules.
- [Effect handlers](references/effect-handlers.md) maps handler names to concrete use-cases.
- [Model inspection](references/model-inspection.md) shows trace, render, relation, and shape workflows.
- [Troubleshooting](references/troubleshooting.md) covers predictable model-construction failures.
- [Model trace smoke](scripts/model_trace_smoke.py) is a small assertion-backed diagnostic script.
