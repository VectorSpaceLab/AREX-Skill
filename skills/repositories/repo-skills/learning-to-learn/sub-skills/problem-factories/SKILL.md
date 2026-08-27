---
name: "problem-factories"
description: "Routes built-in optimizee problem selection, data-backed problem
  setup, custom loss factories, and util.get_config mappings."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# problem-factories

Use this sub-skill when you need to choose, inspect, or author an optimizee problem in `learning-to-learn`.

## Route here for

- Built-in factories: `simple`, `simple_multi_optimizer`, `quadratic`, `ensemble`, `mnist`, and `cifar10`.
- README-facing problem names: `simple`, `simple-multi`, `quadratic`, `mnist`, `cifar`, and `cifar-multi`.
- `util.get_config(problem_name, path=None)` mappings, checkpoint path rules, and optimizer-network assignments.
- Custom problem factories that need dataset setup, queue creation, or stable variable naming.

## Do not handle here

- Meta-loss construction, variable interception, or optimizer assignment mechanics. Use the `meta-optimizer-api` sub-skill.
- Training/evaluation CLI loops, epoch scheduling, or save/eval flow. Use the `training-evaluation` sub-skill.
- Network class internals or preprocessing modules. Use the `optimizer-networks` sub-skill.

## Read first

- `references/problem-catalog.md`
- `references/data-and-custom-problems.md`
- `references/troubleshooting.md`
- `scripts/inspect_problem_config.py`

## Bundled script

- `scripts/inspect_problem_config.py` — inspect a problem name, print a safe config summary, and avoid MNIST/CIFAR downloads by default.

## Working rule

1. Pick the public problem name or source factory you actually need.
2. Check the catalog entry for its variables, side effects, and util mapping.
3. If the problem is data-backed, confirm whether a path will trigger dataset loading or checkpoint lookup.
4. Keep Python side effects outside the returned zero-arg loss builder.
5. If the issue is really optimizer routing or training flow, hand off to the sibling sub-skill instead.
