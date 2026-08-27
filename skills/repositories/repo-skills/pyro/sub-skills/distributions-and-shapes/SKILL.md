---
name: distributions-and-shapes
description: "Choose Pyro distributions and debug batch, event, plate, support,
  and transform shapes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Distributions And Shapes

Use this sub-skill when the user needs to choose a `pyro.distributions`
distribution, reason about `sample_shape`, `batch_shape`, `event_shape`, or
`pyro.plate` dimensions, add constraints/transforms, or debug `log_prob`, support,
validation, NaN/Inf, HMM, stable, zero-inflated, mixture, matching, or CUDA shape
issues.

## Route First

- For distribution selection, Pyro-specific distribution families, constructor
  signatures, constraints/transforms, LKJ, HMM, matching, stable, mixture, and
  optional SciPy caveats, read
  [references/distribution-catalog.md](references/distribution-catalog.md).
- For shape algebra, `plate` dimension placement, `.to_event()`/`Independent`,
  observation shape checks, trace shape diagnostics, and HMM/zero-inflated shape
  recipes, read [references/shapes-and-plates.md](references/shapes-and-plates.md).
- For concrete recovery steps after errors such as invalid support, argument
  constraint violations, invalid `log_prob` shape, NaNs/Infs, CUDA device
  mismatches, SciPy-dependent helper failures, and HMM duration/broadcast
  mistakes, read [references/troubleshooting.md](references/troubleshooting.md).

## Best-Fit Tasks

Use this sub-skill for requests like:

- "which Pyro distribution should I use for zero-inflated counts, correlations,
  an HMM, a stable process, a matching, or a mixture?";
- "why does `log_prob()` have the wrong shape under `plate`?";
- "should this tensor dimension be a batch dim, event dim, or plate dim?";
- "fix `ValueError: invalid log_prob shape`, `expected value argument...`,
  `components event_shape disagree`, or an HMM `duration` mismatch";
- "use `constraints`, `transform_to`, `biject_to`, or `TransformedDistribution`
  safely";
- "make the same distribution code work on CPU and optional CUDA".

## Boundaries And Reroutes

- Basic `pyro.sample`, `pyro.param`, `pyro.plate` introductions, parameter-store
  lifecycle, `PyroModule`, and observation basics: route to
  `../modeling-basics/`.
- SVI, ELBO choice, autoguides, optimizers, and training-loop decisions: route to
  `../svi-and-autoguides/` after this sub-skill has resolved distribution and
  shape contracts.
- MCMC/NUTS/HMC, initialization strategies, posterior prediction, and predictive
  sample shapes: route to `../mcmc-and-prediction/` after this sub-skill has
  resolved support and transform constraints.
- Poutine handler composition, enumeration, `config_enumerate`, `infer_discrete`,
  `TraceEnum_ELBO`, and enum dimension allocation: route to
  `../effect-handlers-and-enumeration/`.
- Domain-specific contributed workflows and optional integrations such as funsor,
  Horovod, Lightning, Graphviz, torchvision, pandas, scanpy, or zuko: route to
  `../contrib-and-domain-workflows/` and treat them as optional unless the active
  environment proves support.

## High-Value Checks Before Answering

1. Start with the support and event type: real scalar, positive scalar, simplex,
   vector, matrix/correlation, integer count, category, sequence/HMM, matching,
   or transformed variable.
2. Inspect `d.batch_shape`, `d.event_shape`, `d.shape(sample_shape)`, and
   `d.log_prob(value).shape` before proposing a `plate` or `.to_event()` fix.
3. Keep Pyro validation enabled while debugging; pass `validate_args=True` for a
   single suspect distribution if global validation is uncertain.
4. Every non-event batch dimension in a Pyro sample site must be declared by an
   enclosing `pyro.plate` or deliberately reinterpreted with `.to_event()`.
5. For observed data, require `obs` to broadcast to
   `fn.batch_shape + fn.event_shape`; `obs_mask` broadcasts only to
   `fn.batch_shape`.
6. Treat CUDA, SciPy-backed helpers, and flow/domain extras as optional; do not
   claim they are available merely because CPU Pyro imports.
