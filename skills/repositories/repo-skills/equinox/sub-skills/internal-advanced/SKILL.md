---
name: internal-advanced
description: "Use semi-public equinox.internal helpers for advanced JAX-library workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Internal Advanced

Use this sub-skill only for advanced tasks that explicitly need
`equinox.internal` (`import equinox.internal as eqxi`). This namespace is
semi-public, intended for expert users and downstream JAX libraries, and has no
stability guarantees.

## Use when

- The user names `equinox.internal`, `eqxi`, `noinline`, internal `while_loop`,
  internal `scan`, `nontraceable`, `nondifferentiable`, `closure_to_pytree`,
  `finalise_jaxpr`, `str2jax`, `GetKey`, or primitive authoring helpers.
- The task is about reducing JAX compile-time by preventing inlining.
- A downstream library needs checkpointed/bounded loops or recursive
  checkpointed scan behavior.
- A custom primitive must support filtered PyTree arguments, JVP, transpose, or
  batching rules.
- A task needs advanced diagnostics that are not exposed as a stable root API.

## Route elsewhere first

- Use `../module-and-trees/` for ordinary module and PyTree patterns.
- Use `../filtered-transformations/` for public filtered JIT/AD/vmap/pmap,
  checkpointing, callback, and sharding APIs.
- Use `../nn-and-state/` for neural-network layers and state.
- Use `../diagnostics-and-serialization/` for public debug, runtime-error,
  progress-meter, and serialization workflows.

## Read first

- [`references/internal-advanced.md`](references/internal-advanced.md) for supported internal families and safe
  usage patterns.
- [`references/troubleshooting.md`](references/troubleshooting.md) for CPU-only, transform, loop, and primitive
  failure modes.
- [`../../references/api-reference.md`](../../references/api-reference.md) for signature summaries.

## Core workflow

1. Confirm a public `eqx.*` API cannot solve the task. Prefer stable APIs when
   possible.
2. Identify the specific internal helper and its expected transform context.
3. Keep tests small and CPU-first unless the user provides accelerator-specific
   acceptance criteria.
4. For `noinline`, verify eager, `jit`, `vmap`, and AD behavior separately.
5. For internal loops, choose `kind="lax"`, `"bounded"`, or
   `"checkpointed"` based on gradient and memory needs.
6. For nontraceable/nondifferentiable helpers, explicitly state which transforms
   are meant to fail.
7. For primitive helpers, define and test impl, abstract eval, JVP, transpose,
   batching, and filtered binding rules.

## Minimal validation

From the generated skill root (set `EQUINOX_SKILL_ROOT` to its absolute path),
run:

```bash
cd "$EQUINOX_SKILL_ROOT" && python scripts/smoke.py --mode internal
```

This checks tiny `noinline`, internal `while_loop`, internal `scan`, and
`nontraceable` behavior. It is a smoke test, not a guarantee that advanced
JAX-internal behavior works for every backend.

## Scope note

This sub-skill distills selected advanced Equinox internals into the bundled
references and smoke helper. The source repository's internal modules and tests
were construction evidence only, not runtime dependencies.

## Key cautions

- `equinox.internal` APIs may change or disappear between releases.
- `noinline` is documented as only tested on CPU. Do not claim accelerator
  support without an accelerator-specific test.
- `to_onnx` is intentionally not a verified capability in this skill because
  the native ONNX test is skipped due to an upstream converter bug.
- Internal loop and primitive helpers depend on JAX internals; pin versions or
  re-run native tests when upgrading JAX or Equinox.
