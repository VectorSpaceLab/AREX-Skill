---
name: flow-authoring
description: "Guides authoring, checking, running, resuming, and debugging local
  Metaflow FlowSpec workflows with parameters, configs, files, foreach, and
  decorators."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Flow Authoring

Use this sub-skill when the task is to create or debug a Metaflow flow script, inspect the flow graph, run locally, resume, or reason about `FlowSpec`, `@step`, `self.next`, parameters, configs, `IncludeFile`, foreach, or local step decorators.

## Quick Route

- Read [`references/workflows.md`](references/workflows.md) for the standard local authoring and CLI loop.
- Read [`references/parameters-and-configs.md`](references/parameters-and-configs.md) for `Parameter`, `JSONType`, `Config`, `config_expr`, and `IncludeFile` behavior.
- Read [`references/advanced-flow-patterns.md`](references/advanced-flow-patterns.md) for foreach, joins, `merge_artifacts`, resume, and local decorators.
- Read [`references/troubleshooting.md`](references/troubleshooting.md) for reserved parameter names, invalid graph transitions, username failures, and file/config issues.
- Run or adapt [`scripts/hello_flow.py`](scripts/hello_flow.py) when you need a self-contained starter flow with parameters and foreach.

## Minimal Flow Pattern

```python
from metaflow import FlowSpec, Parameter, step

class ExampleFlow(FlowSpec):
    count = Parameter("count", default=3, type=int)

    @step
    def start(self):
        self.values = list(range(self.count))
        self.next(self.work, foreach="values")

    @step
    def work(self):
        self.result = self.input * 2
        self.next(self.join)

    @step
    def join(self, inputs):
        self.results = [task.result for task in inputs]
        self.next(self.end)

    @step
    def end(self):
        print(self.results)

if __name__ == "__main__":
    ExampleFlow()
```

Use `python flow.py --no-pylint check` before `run` when lint dependencies are not installed. Use `python flow.py version` for the package version.

## Boundaries

- For `Runner`, `NBRunner`, or programmatic execution, route to [`../runner-and-programmatic/SKILL.md`](../runner-and-programmatic/SKILL.md).
- For reading finished runs, artifacts, tags, logs, metadata providers, or S3 datatools, route to [`../client-and-data/SKILL.md`](../client-and-data/SKILL.md).
- For Cards and `current.card`, route to [`../cards-and-observability/SKILL.md`](../cards-and-observability/SKILL.md).
- For AWS Batch, Kubernetes, Argo, Step Functions, Airflow, schedules, triggers, secrets, or projects, route to [`../deployment-orchestration/SKILL.md`](../deployment-orchestration/SKILL.md).
- For `@pypi`, `@conda`, `--environment`, or package suffixes, route to [`../dependency-environments/SKILL.md`](../dependency-environments/SKILL.md).
