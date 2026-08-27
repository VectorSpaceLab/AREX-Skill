---
name: filtered-transformations
description: "Use Equinox filtered JAX transformations over mixed PyTree models."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Filtered Transformations

Use this sub-skill when applying JAX transforms to Equinox modules or other
mixed PyTrees whose leaves are not all arrays.

## Use when

- A raw `jax.jit`, `jax.grad`, `jax.vmap`, or `jax.pmap` rejects an Equinox
  model or callable PyTree.
- The task names `filter_jit`, `filter_grad`, `filter_value_and_grad`,
  `filter_vmap`, `filter_pmap`, `filter_eval_shape`, `filter_make_jaxpr`,
  `filter_shard`, `filter_checkpoint`, or `filter_pure_callback`.
- The user needs custom filtered derivatives with `filter_custom_jvp` or
  `filter_custom_vjp`.
- A training step must combine filtered gradients, Optax updates, and JIT.
- The task involves pmap/sharding behavior for PyTrees with static leaves.

## Route elsewhere

- Use `../module-and-trees/` when the main task is defining fields,
  partitioning a model manually, or performing tree surgery.
- Use `../nn-and-state/` when the main task is layer construction, `BatchNorm`,
  `Sequential`, `State`, or inference-mode toggles.
- Use `../diagnostics-and-serialization/` for runtime error/debug behavior,
  serialization, or pretty printing.
- Use `../internal-advanced/` for `equinox.internal.noinline`, internal loops,
  primitive authoring helpers, or other semi-public utilities.

## Read first

- [`references/filtered-transformations.md`](references/filtered-transformations.md) for API groups, patterns, and
  examples.
- [`references/troubleshooting.md`](references/troubleshooting.md) for transform-specific failure modes.
- [`../../references/api-reference.md`](../../references/api-reference.md) for signature summaries.

## Core workflow

1. Determine which leaves should be traced as arrays. Equinox defaults usually
   treat JAX/NumPy arrays as dynamic and everything else as static.
2. Replace raw JAX transforms with the corresponding `eqx.filter_*` transform
   when a whole mixed PyTree crosses the transform boundary.
3. Use `eqx.partition`/`eqx.combine` only when you need explicit control or a
   raw JAX transform API.
4. For training steps, put loss, gradient computation, optimizer update, and
   `eqx.apply_updates` inside one compiled function when possible.
5. For batched models, remember that most `equinox.nn` layers act on one example;
   use `jax.vmap` or `eqx.filter_vmap` around the call.
6. For `filter_pmap` or `filter_shard`, check the device/sharding assumptions
   before declaring backend coverage.

## Minimal validation

From the generated skill root (set `EQUINOX_SKILL_ROOT` to its absolute path),
run the bundled smoke helper after installing Equinox:

```bash
cd "$EQUINOX_SKILL_ROOT" && python scripts/smoke.py --mode transformations
```

For CPU multi-device `filter_pmap` smoke coverage:

```bash
cd "$EQUINOX_SKILL_ROOT" && python scripts/smoke.py --mode transformations --two-cpu-devices
```

The helper configures two logical CPU devices before importing JAX when that
flag is supplied.

## Scope note

This sub-skill distills Equinox's filtered transform behavior into the bundled
references and smoke helper. The source repository and its test/docs checkout
were construction evidence only, not runtime dependencies.
## Key cautions

- A CPU `filter_pmap` smoke validates API structure, not accelerator semantics.
- `filter_grad` differentiates floating-point/complex array leaves in the first
  argument and returns a PyTree matching that input; nondifferentiable/static
  leaves appear as `None` gradients.
- Donation options are explicit: `filter_jit` supports `donate="all"`,
  `"all-except-first"`, warning variants, and `"none"`; `filter_pmap` supports
  `"all"`, `"warn"`, and `"none"`.
- If a problem is actually about layer state or batch normalization axes, route
  to `nn-and-state` after confirming the transform boundary.
