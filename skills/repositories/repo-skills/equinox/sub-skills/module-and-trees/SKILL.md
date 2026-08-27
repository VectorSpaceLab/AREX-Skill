---
name: module-and-trees
description: "Use Equinox modules, fields, PyTree filtering, and tree surgery correctly."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Module and Trees

Use this sub-skill for Equinox’s core model-as-PyTree abstraction and the
utilities that manipulate mixed PyTrees.

## Use when

- The user is defining or debugging an `eqx.Module` subclass.
- A model has JAX arrays plus Python functions, strings, booleans, or other
  non-array leaves.
- The task mentions `eqx.field`, converters, static fields, `AbstractVar`,
  `AbstractClassVar`, or `__check_init__`.
- The task asks for model surgery with `tree_at`, trainable/static partitioning,
  `tree_equal`, `tree_check`, `apply_updates`, or `Partial`.
- A task needs to prepare a model PyTree for Optax, JAX transforms, or
  serialization.

## Route elsewhere

- Use `../filtered-transformations/` when the main issue is `filter_jit`,
  `filter_grad`, `filter_vmap`, `filter_pmap`, AD, callbacks, or sharding.
- Use `../nn-and-state/` for built-in `equinox.nn` layers, stateful modules,
  `Shared`, and inference-mode behavior.
- Use `../diagnostics-and-serialization/` for saving/loading leaves, runtime
  errors, pretty printing, progress meters, or debug tools.
- Use `../internal-advanced/` only for semi-public `equinox.internal` helpers.

## Read first

- [`references/module-and-trees.md`](references/module-and-trees.md) for module patterns, API decisions, and
  model-surgery recipes.
- [`references/troubleshooting.md`](references/troubleshooting.md) for common `eqx.Module`, static-field,
  converter, and mixed-leaf failures.
- [`../../references/api-reference.md`](../../references/api-reference.md) for a cross-skill symbol index.

## Core workflow

1. Identify the PyTree boundary. Decide which values are array leaves,
   non-array dynamic objects, or static metadata.
2. Define an `eqx.Module` subclass with annotated fields. Use a custom
   `__init__` only when construction logic needs it; otherwise rely on dataclass
   initialization.
3. Mark metadata such as strings, booleans, shapes, or callables with
   `eqx.field(static=True)` when it should not be a PyTree leaf.
4. Use `eqx.field(converter=...)` for safe field normalization at initialization
   time.
5. Use `__check_init__` for invariant checks; do not mutate fields inside it.
6. Split trainable and static leaves with `eqx.partition` or `eqx.filter`,
   using predicates such as `eqx.is_inexact_array`, before optimizers or raw
   JAX transforms.
7. Use `eqx.tree_at` for out-of-place surgery such as replacing a final layer,
   changing an initializer result, or toggling nested leaves.
8. Validate structure with `eqx.tree_check` and compare expected outputs with
   `eqx.tree_equal`.

## Minimal validation

From the generated skill root (set `EQUINOX_SKILL_ROOT` to its absolute path),
run the bundled smoke helper after installing Equinox:

```bash
cd "$EQUINOX_SKILL_ROOT" && python scripts/smoke.py --mode module
```

This checks module construction, static-field preservation, partition/combine,
`tree_at`, and `tree_check` using only the installed package and bundled runtime
files.

## Scope note

This sub-skill distills Equinox's public module, filter, tree-manipulation, and
training-update behavior into the bundled references. Future agents should use
`references/module-and-trees.md`, `references/troubleshooting.md`, and
`scripts/smoke.py`; the source repository was construction evidence only, not a
runtime dependency.

## Key cautions

- An Equinox module is a frozen dataclass and a PyTree. Treat object identity as
  secondary to tree value and structure.
- Plain `jax.jit` and `jax.grad` are valid only when their dynamic arguments are
  all JAX-compatible leaves. Use filtered transforms for mixed modules.
- Do not store bound methods on a module field; use a property or wrapper.
- Do not mark trainable arrays static just to silence JAX errors; filter the
  model instead.
