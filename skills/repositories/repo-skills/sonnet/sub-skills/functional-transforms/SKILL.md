---
name: functional-transforms
description: "Use Sonnet's functional transform API for stateless-style modules,
  gradients, jit/device helpers, and functional optimizers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Functional Transforms

Use this sub-skill for `snt.functional.variables`, `transform`, `transform_with_state`, `without_state`, `grad`, `value_and_grad`, `jit`, `device_put`, `device_get`, TensorVariable behavior, parameter/state dictionaries, and functional optimizers.

## Start here

- [references/api-reference.md](references/api-reference.md): signatures, returned objects, TensorVariable semantics, and optimizer state.
- [references/workflows.md](references/workflows.md): transform init/apply, state threading, gradients, and one-step functional optimizer recipes.
- [references/troubleshooting.md](references/troubleshooting.md): no-value TensorVariable errors, forgotten init, params/state confusion, and device surprises.
- [scripts/sonnet_functional_transform_smoke.py](scripts/sonnet_functional_transform_smoke.py): synthetic functional MLP + Adam smoke.

## Boundaries

- Object-oriented modules: [../module-authoring/SKILL.md](../module-authoring/SKILL.md).
- Object-oriented optimizer loops: [../training-and-optimization/SKILL.md](../training-and-optimization/SKILL.md).
- Backend/device verification: [../serialization-and-distribution/SKILL.md](../serialization-and-distribution/SKILL.md).

## Minimal protocol

Create modules inside `fn.variables()`, wrap a function with `fn.transform` or `fn.transform_with_state`, call `init` before `apply`, carry returned `params` and `state` explicitly, and use `fn.value_and_grad` plus a functional optimizer when the task wants stateless-style updates.
