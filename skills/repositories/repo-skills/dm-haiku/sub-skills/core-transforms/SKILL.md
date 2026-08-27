---
name: core-transforms
description: "Use Haiku transforms to choose pure init/apply wrappers, state/RNG
  signatures, shared multi-method transforms, and validation checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Core Transforms

Use this sub-skill when a task asks how to turn a Haiku function into pure JAX-callable functions, choose between stateless and stateful init/apply signatures, remove an unused apply RNG, share one initialization across multiple apply methods, or diagnose transform argument ordering.

## Route here for

- `hk.transform` and `hk.transform_with_state` selection.
- `init`/`apply` argument order, especially where `rng` and `state` go.
- `hk.without_apply_rng`, `hk.without_state`, and `hk.with_empty_state` wrapper decisions.
- `hk.multi_transform` and `hk.multi_transform_with_state` for multiple apply methods sharing parameters/state.
- `hk.running_init()` checks and lightweight shape validation of transformed functions.

## Route elsewhere

- Module subclass design, parameter trees, `hk.get_parameter`, `hk.get_state`, `hk.set_state`, and direct RNG APIs belong in sibling sub-skill `params-state-rng`.
- Layer catalogs, built-in networks, `hk.BatchNorm` configuration, attention/RNNs, and full model examples belong in `modules-and-networks`.
- Haiku wrappers for JAX transforms or control flow inside transformed functions, such as `hk.vmap`, `hk.scan`, `hk.grad`, `hk.switch`, and lifting, belong in `jax-interop-and-advanced`.

## Read and run

- Read [references/api-reference.md](references/api-reference.md) when you need exact transform signatures, return contracts, or a quick decision table.
- Read [references/workflows.md](references/workflows.md) when implementing or migrating stateless, stateful, no-apply-rng, multi-method, or `running_init` workflows.
- Read [references/troubleshooting.md](references/troubleshooting.md) when `init`/`apply` argument order, missing state, missing RNG, or JAX tracing errors are suspected.
- Run [scripts/haiku_transform_smoke.py](scripts/haiku_transform_smoke.py) to verify a local Haiku/JAX install with deterministic stateless, stateful, multi-transform, and `running_init` checks.

## Fast transform choice

1. Start with the untransformed function `f(*args, **kwargs)` that creates or calls Haiku modules inside the function body.
2. If `f` never calls `hk.get_state` or `hk.set_state` and does not use stateful modules, use `hk.transform(f)`.
3. If `f` creates, reads, or updates state, use `hk.transform_with_state(f)` and thread the returned `state` through every apply call.
4. If the apply path does not use `hk.next_rng_key`, stochastic modules, dropout, or random sampling, wrap the transformed object with `hk.without_apply_rng(...)`; remember that `init` still receives `rng` first.
5. If several apply methods must share one module/parameter set, use `hk.multi_transform` or `hk.multi_transform_with_state` with a factory that returns `(template_init_fn, apply_fn_tree)`.
6. Validate with a tiny input: assert output shapes, inspect `jax.tree.map(lambda x: x.shape, params)`, and for stateful transforms assert both input and output state structures.

## Purity expectations

Haiku transforms produce pure `init` and `apply` functions that explicitly receive parameters, state, and RNG. Apply JAX transformations such as `jax.grad` or `jax.jit` to the returned `init`/`apply` functions rather than passing an already JAX-transformed function into `hk.transform`. If a raw JAX transform/control-flow primitive appears inside a transformed function and interacts with Haiku state/RNG/module creation, route to `jax-interop-and-advanced` for Haiku wrapper guidance.
