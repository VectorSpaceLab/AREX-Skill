---
name: equinox
description: "Operating skill for the Equinox JAX neural-network and PyTree library."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Equinox

Equinox is a JAX library for building models as PyTrees, applying filtered JAX
transformations, and using reusable neural-network layers, stateful modules,
and advanced debugging utilities.

Use this skill when the user mentions:

- `equinox`, `eqx`, `eqx.Module`, or `equinox.nn`
- filtered transforms such as `filter_jit`, `filter_grad`, `filter_vmap`, or
  `filter_pmap`
- model surgery, PyTree partitioning, serialization, or runtime errors
- `Sequential`, `MLP`, `BatchNorm`, `State`, `Shared`, or `inference_mode`
- `equinox.internal` helpers such as `noinline`, `while_loop`, or `scan`

## Quick start

Install the public package with:

```bash
pip install equinox
```

For a local checkout or a health check, run the bundled [`scripts/smoke.py`](scripts/smoke.py)
from the generated skill root (the directory containing this `SKILL.md`). Set
`EQUINOX_SKILL_ROOT` to that absolute directory and keep it as the command
working directory:

```bash
cd "$EQUINOX_SKILL_ROOT" && python scripts/smoke.py --mode all
```

If you need multi-device CPU coverage for `pmap` or sharding checks, add
`--two-cpu-devices` to the smoke script.

## Route map

### [`sub-skills/module-and-trees`](sub-skills/module-and-trees/SKILL.md)
Use for `eqx.Module`, field declarations, abstract attributes, PyTree filtering,
`tree_at`, `tree_equal`, `tree_check`, `apply_updates`, `Partial`, and model
surgery.

### [`sub-skills/filtered-transformations`](sub-skills/filtered-transformations/SKILL.md)
Use for `filter_jit`, `filter_grad`, `filter_vmap`, `filter_pmap`, `filter_eval_shape`,
`filter_make_jaxpr`, custom filtered AD, checkpointing, callbacks, and sharding
behavior.

### [`sub-skills/nn-and-state`](sub-skills/nn-and-state/SKILL.md)
Use for `equinox.nn` layers, `Sequential`, `Lambda`, `MLP`, `BatchNorm`,
`State`, `StateIndex`, `Shared`, and inference-mode workflows.

### [`sub-skills/diagnostics-and-serialization`](sub-skills/diagnostics-and-serialization/SKILL.md)
Use for `tree_serialise_leaves`, `tree_deserialise_leaves`, runtime errors,
debug tools, pretty printing, enumerations, progress meters, and package
troubleshooting.

### [`sub-skills/internal-advanced`](sub-skills/internal-advanced/SKILL.md)
Use only for advanced or downstream-library work with `equinox.internal`,
including `noinline`, `while_loop`, `scan`, `nontraceable`, `finalise_jaxpr`,
and primitive authoring helpers.

## How to choose

- If the task is about model shape, PyTree composition, or field semantics,
  start with `module-and-trees`.
- If the task is about JAX transforms crossing model boundaries, start with
  `filtered-transformations`.
- If the task is about built-in layers, training loops, or stateful modules,
  start with `nn-and-state`.
- If the task is about debugging, serialization, or runtime checks, start with
  `diagnostics-and-serialization`.
- If the task explicitly names `equinox.internal` or an advanced helper that is
  not part of the everyday public API, start with `internal-advanced`.

## Reading order

1. Read the sub-skill that matches the dominant workflow.
2. Use the linked reference file in that sub-skill for API details, examples,
   and troubleshooting.
3. Use [`references/api-reference.md`](references/api-reference.md) when you need a cross-skill API index.
4. Use [`references/troubleshooting.md`](references/troubleshooting.md) when the issue looks like install/import,
   backend, optional dependency, or mixed-leaf JAX behavior. Read [`references/repo-provenance.md`](references/repo-provenance.md)
   before relying on version-sensitive guidance.

## Common signals

- A plain `jax.jit` or `jax.grad` call fails because a model contains non-array
  leaves: route to `filtered-transformations`.
- A module definition fails because fields or abstract attributes are missing:
  route to `module-and-trees`.
- A layer needs `state` or `axis_name`, or `Sequential` has a stateful layer:
  route to `nn-and-state`.
- A runtime error, serialization round-trip, or debug trace is the focus:
  route to `diagnostics-and-serialization`.
- A user asks about `noinline`, `while_loop`, `scan`, or other semi-public
  helpers: route to `internal-advanced`.

## Notes

- Equinox is intentionally PyTree-first: models, helper wrappers, and advanced
  utilities all depend on ordinary JAX semantics rather than a separate runtime.
- There is no repo CLI. Treat library installation, import checks, and API
  inspection as the primary entry points.
- Prefer the bundled references over source checkout links so the skill stays
  usable after the repository is no longer present.
