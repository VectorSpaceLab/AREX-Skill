---
name: core-api-and-autograd
description: "Use Jittor's core Var, Module, Function, gradient, execution, and
  serialization APIs for tensor and autograd tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Core API and autograd

Use this sub-skill when a task is about Jittor tensor creation, `Var` arithmetic, broadcasting, gradients, execution order, `Module` or `Function` behavior, synchronization, or basic serialization.

Do **not** use it for layer/optimizer training recipes, dataset/model zoo workflows, backend installation and debugging, or custom C++ operator authoring. Route those to the sibling sub-skills that own them.

## Read or run map

- Read [core API reference](references/core-api-reference.md) for the verified public signatures, construction helpers, `Module`/`Function` surface, and common shape or dtype expectations.
- Read [autograd and execution](references/autograd-and-execution.md) for lazy execution, `data`/`sync` behavior, gradient updates, and safe no-grad scopes.
- Read [troubleshooting](references/troubleshooting.md) when you see shape mismatches, dtype surprises, retained graphs, serialization problems, or confusing lazy-execution errors.
- Run [core_api_smoke.py](scripts/core_api_smoke.py) for a tiny deterministic CPU smoke that exercises `Var`, `Module`, gradients, and state transfer.

## What this sub-skill owns

- `jt.array`, `jt.float32`, `jt.zeros`, `jt.ones`, `jt.rand`, `jt.random`, and similar core constructors.
- `Var` operations, broadcasting, `data`, `numpy`, `sync`, `name`, and simple reductions.
- `jt.grad`, `jt.no_grad`, `jt.enable_grad`, `jt.flag_scope`, lazy execution choices, and `jt.sync_all`.
- `jt.Module`, `jt.Function`, parameter/state layout, and checkpoint save/load basics.
- Minimal core debugging for graph liveness, accidental graph retention, and shape/dtype mistakes.

## Quick start

1. Create or import a tiny `Var` and confirm the result synchronizes correctly.
2. If you need gradients, compute a scalar loss and call `jt.grad` on the target vars.
3. Use `Module.execute`, not `forward`.
4. Save and load only public state; keep private caches and generated values out of the model state.
5. If behavior looks wrong, read the autograd/execution reference before changing the model logic.

## Baseline check

A normal CPU baseline for this sub-skill is the bundled smoke script:

```bash
python scripts/core_api_smoke.py --help
python scripts/core_api_smoke.py
```

The script should stay tiny and deterministic; it is meant to confirm the public API shape, not to benchmark or train a model.