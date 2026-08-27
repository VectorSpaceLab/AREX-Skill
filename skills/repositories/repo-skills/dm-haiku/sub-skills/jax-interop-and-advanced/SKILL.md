---
name: jax-interop-and-advanced
description: "Use this dm-haiku sub-skill for Haiku-aware JAX transform
  wrappers, nested transform lifting, data-structure utilities, mixed precision,
  summaries, visualization, config, and testing helpers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# JAX interop and advanced Haiku utilities

Use this sub-skill when the task involves Haiku-specific wrappers around JAX transforms or advanced support utilities rather than ordinary layer selection or basic `hk.transform` signatures.

## Read this when

- A Haiku function uses `hk.get_parameter`, `hk.get_state`, `hk.set_state`, or `hk.next_rng_key` inside `vmap`, `scan`, `grad`, `remat`, control flow, or shape evaluation.
- You need to rewrite raw `jax.vmap`, `jax.lax.scan`, `jax.remat`, or JAX control flow used inside a transformed Haiku function.
- You need `hk.lift`, `hk.lift_with_state`, `hk.transparent_lift`, or `hk.layer_stack` for nested transforms, ensembles, or repeated per-layer blocks.
- You need to filter, partition, merge, traverse, count, or convert Haiku parameter/state dictionaries for freezing or optimizer grouping.
- You need Haiku mixed precision, DOT graphs, summaries, `jaxpr_info`, configuration flags, or `hk.testing.transform_and_run`.

## Route elsewhere

- For choosing between `hk.transform`, `hk.transform_with_state`, `hk.without_apply_rng`, stateful apply signatures, or multi-transform basics, use the `core-transforms` sub-skill.
- For ordinary `hk.Module` authoring, parameter/state/RNG direct APIs, naming, and interceptors, use the `params-state-rng` sub-skill.
- For common layer catalogs, `hk.nets`, RNNs, attention, convolution, normalization, and example-derived model-building patterns, use the `modules-and-networks` sub-skill.
- For `haiku.experimental.flax` APIs and variable collection mapping between Haiku and Flax, use the `flax-interop` sub-skill.

## Bundled references and script

- Read [references/jax-transform-wrappers.md](references/jax-transform-wrappers.md) when replacing raw JAX transforms/control flow, choosing `hk.vmap`/`hk.scan`/`hk.remat`, using `hk.lift*`, or applying `hk.layer_stack`.
- Read [references/utilities-reference.md](references/utilities-reference.md) when manipulating Haiku parameter/state structures, using mixed precision, producing summaries/graphs, tuning config flags, or writing small Haiku tests.
- Read [references/troubleshooting.md](references/troubleshooting.md) when you see tracer leaks, state/RNG leakage, lift name collisions, optional visualization/JAX2TF dependency failures, mixed precision contamination, or partition/merge mistakes.
- Run [scripts/haiku_jax_transform_smoke.py](scripts/haiku_jax_transform_smoke.py) to validate that the current environment can execute safe `hk.vmap`, `hk.scan`, and `hk.data_structures.partition`/`merge` examples on synthetic arrays without Graphviz, TensorFlow, or datasets.

## Operating rules

1. Prefer raw `jax.*` transforms outside Haiku after a function has been transformed into pure `init`/`apply` functions.
2. Inside a transformed Haiku function, use the Haiku wrapper (`hk.vmap`, `hk.scan`, `hk.remat`, `hk.cond`, and friends) whenever the mapped/scanned/rematted/branched function touches Haiku params, state, RNG, or modules.
3. Keep parameter and state structure stable across JAX control-flow branches and loop iterations. If a branch or loop might not run during init, create needed modules unconditionally under `hk.running_init()`.
4. Treat advanced helpers as scoped tools: clear or context-manage mixed precision policies, keep Graphviz/TensorFlow rendering optional, and run synthetic smoke checks before relying on advanced wrappers in larger experiments.
