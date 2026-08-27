---
name: meta-optimizer-api
description: "Route graph construction, unroll, save/load, and debugging work
  for MetaOptimizer."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Meta Optimizer API

Use this sub-skill when a task needs to build, inspect, unroll, save, load, or debug `meta.MetaOptimizer`, `meta_loss`, or `meta_minimize`.

## Start here
- [API reference](references/api-reference.md)
- [Unroll workflows](references/meta-unroll-workflows.md)
- [Troubleshooting](references/troubleshooting.md)
- [Smoke script](scripts/build_meta_optimizer_smoke.py)

## Covered responsibilities
- `MetaOptimizer(**kwargs)` network registry setup
- `meta_loss(make_loss, len_unroll, net_assignments=None, second_derivatives=False)`
- `meta_minimize(make_loss, len_unroll, learning_rate=0.01, **kwargs)`
- `MetaLoss` and `MetaStep` field semantics
- variable interception and optimizee-variable ordering
- `net_assignments` rules, including exact names and overlapping mappings
- `.l2l` save/load behavior for optimizer state

## Route elsewhere
- Optimizer network classes and preprocessing details -> optimizer-networks
- Built-in/custom problem factories and dataset setup -> problem-factories
- CLI train/eval loops and saved-optimizer workflows -> training-evaluation

## Working rule of thumb
1. Make `make_loss` pure graph construction.
2. Match variable names exactly when assigning nets.
3. Call `reset` before each new epoch or task.
4. Call `update` after each unroll if the live optimizee state should advance.
5. Use the smoke script before deeper debugging.
