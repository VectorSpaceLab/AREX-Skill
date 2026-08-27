---
name: operator-hub-and-cli
description: "Operate Towhee ops wrappers, local operator registration, Hub
  revisions, and CLI help validation without unsafe downloads or server
  startup."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Operator Hub and CLI

Use this sub-skill when a task needs Towhee operator lookup, local operator development boundaries, Hub operator version selection, `towhee init` guidance, package entry points, or help-only CLI validation.

## Fast routing

- For operator names, wrapper behavior, local registration, `PyOperator`, and `NNOperator` boundaries, use [references/operator-api.md](references/operator-api.md).
- For `towhee`, `towhee init`, `towhee server --help`, `python -m towhee`, and package entry points, use [references/cli-reference.md](references/cli-reference.md).
- For failure triage around `pkg_resources`, Hub downloads/cache, accidental server startup, template writes, registry naming, and NN training prerequisites, use [references/troubleshooting.md](references/troubleshooting.md).
- To validate the installed CLI safely, run [scripts/check_cli_help.py](scripts/check_cli_help.py). The script checks help output only and must not start servers or initialize templates.

## Boundaries and handoff

- Route neural-network training loops, trainer configs, model zoo dependencies, and extended `NNOperator.train()` usage to [training-and-models](../training-and-models/SKILL.md).
- Route live `towhee server` startup, HTTP/GRPC clients, Triton, Docker, and port management to [serving-and-triton](../serving-and-triton/SKILL.md).
- Route pipeline node composition, schemas, batching, flush/debug/profiling, and `pipe.input(...).map(...).output(...)` design to [pipeline-programming](../pipeline-programming/SKILL.md).
- Do not use Hub downloads, `towhee init`, or live servers as routine validation unless the user explicitly requests those side effects and supplies an isolated target.

## Minimum safe operating pattern

```python
from towhee import ops, register
from towhee.operator import PyOperator, NNOperator

@register(name='add_operator')
class AddOperator(PyOperator):
    def __init__(self, factor):
        self.factor = factor

    def __call__(self, x):
        return x + self.factor

op = ops.add_operator(10)   # lazy wrapper; loads when called
assert op(2) == 12
```

Prefer pinned Hub revisions for reproducibility:

```python
op = ops.some_namespace.some_operator().revision('main')
```

Use `.latest()` only when intentionally refreshing a cached Hub operator.
