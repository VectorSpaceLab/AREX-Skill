---
name: diagnostics-and-serialization
description: "Use Equinox serialization, runtime errors, debug tools, pretty
  printing, enumerations, and progress meters."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Diagnostics and Serialization

Use this sub-skill for saving/loading PyTrees, runtime checks, debugging JAX
transforms, pretty-printing modules, enumerations, progress meters, and cache
maintenance.

## Use when

- The user needs `tree_serialise_leaves`, `tree_deserialise_leaves`, or custom
  serialization filter specs.
- A task asks about runtime checks with `error_if` or `branched_error_if`.
- A JAX/Equinox program has NaNs, repeated tracing, dead-code elimination, or
  confusing transformed error output.
- The user needs `tree_pformat`, `tree_pprint`, `Enumeration`, `clear_caches`,
  or progress meter utilities.
- The task asks whether ONNX export is supported by the current repo evidence.

## Route elsewhere

- Use `../module-and-trees/` for model field definitions, PyTree partitioning,
  `tree_at`, or `tree_check` as model-construction tools.
- Use `../filtered-transformations/` when the main task is compiling,
  differentiating, vmapping, pmapping, or sharding a mixed PyTree.
- Use `../nn-and-state/` for layers, training/evaluation state, dropout,
  `BatchNorm`, or tied weights.
- Use `../internal-advanced/` for `equinox.internal` loops, primitive helpers,
  or `noinline`.

## Read first

- [`references/diagnostics-and-serialization.md`](references/diagnostics-and-serialization.md) for patterns and API usage.
- [`references/troubleshooting.md`](references/troubleshooting.md) for serialization, runtime error, debug, and
  optional dependency failures.
- [`../../references/troubleshooting.md`](../../references/troubleshooting.md) for cross-cutting install/backend notes.

## Core workflow

1. For save/load tasks, identify the full PyTree structure and construct a
   like-tree for deserialization.
2. Use `tree_serialise_leaves` to write serializable leaves and
   `tree_deserialise_leaves` with the like-tree to restore them.
3. Use custom filter specs only when the default array/scalar behavior is not
   enough.
4. For runtime validation inside transformed code, use `eqx.error_if` or
   `eqx.branched_error_if` instead of ordinary Python exceptions.
5. For NaN and recompilation debugging, use `eqx.debug.backward_nan`,
   `eqx.debug.assert_max_traces`, `jax.debug.print`, and targeted environment
   variables.
6. Use `tree_pformat`/`tree_pprint` for readable module and shape diagnostics.

## Minimal validation

From the generated skill root (set `EQUINOX_SKILL_ROOT` to its absolute path),
run:

```bash
cd "$EQUINOX_SKILL_ROOT" && python scripts/smoke.py --mode diagnostics
```

This validates a tiny leaf serialization round-trip, a false runtime-error
branch, pretty printing, and trace counting.

## Scope note

This sub-skill distills Equinox's serialization, runtime-error, and diagnostics
workflows into the bundled references and smoke helper. The source repository's
tests and docs were construction evidence only, not runtime dependencies.

## Key cautions

- Deserialization is structure-sensitive; the like-tree controls structure and
  non-serialized leaves.
- `eqx.error_if` can raise from within JIT/lax regions, but JAX may wrap the
  visible error text.
- Prefer `EQX_ON_ERROR` for breakpoint-mode runtime-error debugging; `on_error=`
  is a per-call override, but `breakpoint` is safest via the environment
  variable.
- Keep the return value from `error_if`/`branched_error_if` in the computation;
  if you drop it, JAX can dead-code-eliminate the check.
- `tqdm` is optional and only needed for the tqdm progress meter.
- ONNX export is not treated as a verified runtime capability because the repo’s
  ONNX test is skipped due an upstream `tf2onnx` issue.
