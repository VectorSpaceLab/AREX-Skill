---
name: nn-and-state
description: "Use Equinox neural-network layers, Sequential models, stateful
  layers, and inference mode."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Neural Networks and State

Use this sub-skill for `equinox.nn` layers and stateful model workflows.

## Use when

- The user asks how to build a model with `eqx.nn.Linear`, `MLP`, `Sequential`,
  `Conv*`, `MultiheadAttention`, `Embedding`, pooling, RNN cells, or
  normalization layers.
- A task needs `Dropout`, `BatchNorm`, `SpectralNorm`, `WeightNorm`,
  `inference_mode`, or explicit PRNG key handling.
- The user needs `eqx.nn.State`, `StateIndex`, `make_with_state`,
  `delete_init_state`, or a custom stateful layer.
- A model needs tied parameters with `eqx.nn.Shared`.
- A training loop combines Equinox layers with `filter_grad`, Optax, and
  `apply_updates`.

## Route elsewhere

- Use `../module-and-trees/` for raw `eqx.Module` field design, tree surgery,
  filtering, and optimizer parameter selection.
- Use `../filtered-transformations/` when the dominant issue is JIT, AD, vmap,
  pmap, callbacks, or sharding.
- Use `../diagnostics-and-serialization/` for saving/loading, runtime errors,
  debug tracing, or pretty printing.
- Use `../internal-advanced/` for semi-public internal loops and primitives.

## Read first

- [`references/nn-and-state.md`](references/nn-and-state.md) for layer families, stateful workflows,
  single-example calling rules, and training-step patterns.
- [`references/troubleshooting.md`](references/troubleshooting.md) for `BatchNorm`, stale `State`, dropout,
  `Sequential`, and shared-weight failures.
- [`../../references/api-reference.md`](../../references/api-reference.md) for cross-skill signatures.

## Core workflow

1. Choose the layer family and confirm whether it is stateless, stochastic, or
   stateful.
2. Remember that most `equinox.nn` layers consume one example. Use `jax.vmap` or
   `eqx.filter_vmap` around layer calls for batches.
3. Use `Sequential` for ordered layers. Wrap activation functions with
   `eqx.nn.Lambda` when they live inside `Sequential`.
4. Pass PRNG keys to constructors and to stochastic calls such as dropout.
5. For stateful layers, construct with `eqx.nn.make_with_state(ModelClass)` and
   thread the returned `State` through every call.
6. Toggle inference behavior with `eqx.nn.inference_mode(model, value=True)`.
7. Use `eqx.nn.Shared` for intentional tied weights instead of relying on object
   identity in a PyTree.
8. For training, combine this sub-skill with `filtered-transformations` and
   `module-and-trees`.

## Minimal validation

From the generated skill root (set `EQUINOX_SKILL_ROOT` to its absolute path),
run:

```bash
cd "$EQUINOX_SKILL_ROOT" && python scripts/smoke.py --mode nn
```

This validates tiny `MLP`, `Sequential`, custom state, and `Shared` examples.
It does not run expensive training or download datasets.

## Scope note

This sub-skill distills Equinox's built-in layer, state, and sharing workflows
into the bundled references and smoke helper. The source repository's tests,
docs, and notebooks were construction evidence only, not runtime dependencies.

## Key cautions

- `BatchNorm` must run inside a `vmap` or `pmap` with a matching `axis_name` for
  training statistics.
- `State.set` and `State.update` return a new state and invalidate the old one.
- `MLP(..., scan=True)` changes the internal representation for compile-time
  reasons; do not call the scanned hidden layer stack directly.
- `Shared` requires matching source/destination structure, shapes, and dtypes.
- Stochastic layers use explicit keys; do not hide key generation inside a JITed
  training step without a reproducible split plan.
