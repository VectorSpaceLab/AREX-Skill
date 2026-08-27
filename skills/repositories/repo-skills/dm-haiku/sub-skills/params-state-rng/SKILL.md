---
name: params-state-rng
description: "Author and debug Haiku Module classes, direct parameter/state
  APIs, RNG keys, naming scopes, and interception hooks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# params-state-rng

Use this sub-skill when you need to write or debug code that lives *inside* a Haiku transformed function and directly creates modules, parameters, mutable state, random keys, names, or API hooks.

## Use this for

- Implementing `hk.Module` subclasses and their `__init__` / `__call__` patterns.
- Creating or reusing values with `hk.get_parameter`, `hk.get_state`, and `hk.set_state`.
- Debugging Haiku parameter/state tree keys, module names, name scopes, and parameter sharing.
- Managing stochastic code with `hk.PRNGSequence`, `hk.next_rng_key`, `hk.next_rng_keys`, and `hk.maybe_next_rng_key`.
- Applying advanced hooks: `hk.custom_creator`, `hk.custom_getter`, `hk.custom_setter`, and `hk.intercept_methods`.

## Route away when

- Choosing `hk.transform`, `hk.transform_with_state`, `hk.without_apply_rng`, or multi-transform wrappers: use the `core-transforms` sub-skill.
- Selecting built-in layers, networks, attention, convolutions, normalization, or RNN modules: use the `modules-and-networks` sub-skill.
- Wrapping Haiku state/RNG through `jax.vmap`, `jax.scan`, `jax.grad`, control flow, lifting, or data-structure utilities: use the `jax-interop-and-advanced` sub-skill.
- Translating Haiku parameters/state to Flax variable collections: use the `flax-interop` sub-skill.

## Operating procedure

1. Confirm that the code using Haiku direct APIs will run inside a transformed function. If not, first choose the correct transform in `core-transforms`.
2. Sketch the expected parameter and state tree keys before coding: outer module/name-scope path first, leaf parameter/state name second.
3. For custom modules, call `super().__init__(name=name)` before creating submodules or values, and create parameters/state inside transformed calls rather than at import time.
4. For state, use `hk.transform_with_state` and pass state into and out of `apply`.
5. For RNG, pass a non-`None` JAX PRNG key to `init` or `apply` whenever `hk.next_rng_key()` may execute; use `hk.maybe_next_rng_key()` only for deliberately optional randomness.
6. Run the bundled smoke script after edits to confirm parameter keys, state updates, and RNG failure/recovery behavior.

## Bundled references and script

- Read [references/api-reference.md](references/api-reference.md) for compact API signatures, tree-key rules, naming behavior, and hook callback contracts.
- Read [references/state-rng-workflows.md](references/state-rng-workflows.md) for end-to-end recipes covering custom modules, stateful counters, stochastic paths, optional RNG, naming, and interception.
- Read [references/troubleshooting.md](references/troubleshooting.md) when you see context, duplicate-name, missing-RNG, mutable-state, or tree-key errors.
- Run [scripts/haiku_rng_state_smoke.py](scripts/haiku_rng_state_smoke.py) to verify a local Haiku/JAX environment with deterministic synthetic parameter, state, and RNG checks.
