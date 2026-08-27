---
name: module-authoring
description: "Author and debug custom Sonnet modules, lazy variables,
  composition wrappers, and module build contracts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Sonnet Module Authoring

Use this sub-skill for custom `snt.Module` classes, `@snt.once` lazy variable creation, variable and submodule inspection, name scopes, `snt.Sequential`, `snt.Deferred`, `snt.BatchApply`, and `snt.build` shape checks.

## Start here

1. Read [references/module-patterns.md](references/module-patterns.md) for concrete authoring patterns.
2. Read [references/api-reference.md](references/api-reference.md) for verified signatures and contracts.
3. Read [references/troubleshooting.md](references/troubleshooting.md) for construction, first-call, and composition failures.
4. Run [scripts/module_contract_smoke.py](scripts/module_contract_smoke.py) for a tiny executable lazy-variable and optional `BatchApply` check.

## Boundaries

- Built-in layers and `snt.nets`: [../layers-and-nets/SKILL.md](../layers-and-nets/SKILL.md).
- Optimizers and training loops: [../training-and-optimization/SKILL.md](../training-and-optimization/SKILL.md).
- Functional `init`/`apply` APIs: [../functional-transforms/SKILL.md](../functional-transforms/SKILL.md).
- Checkpoint/SavedModel/distribution: [../serialization-and-distribution/SKILL.md](../serialization-and-distribution/SKILL.md).

## Minimum module contract

- Subclass `snt.Module` and call `super().__init__(name=name)` in `__init__`.
- Put input-dependent variable creation in a side-effect-only `@snt.once` method that returns `None`.
- Call/build the module before inspecting `variables` or `trainable_variables`.
- Use explicit subclasses for branching or extra call arguments; use `Sequential` only for plain chains.
- Use `Deferred` when one module's constructor depends on another module after first call, and `BatchApply` for applying a 2-D module over extra leading dimensions.
