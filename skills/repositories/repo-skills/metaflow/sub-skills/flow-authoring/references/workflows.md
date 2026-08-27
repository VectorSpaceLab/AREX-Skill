# Local Flow Authoring Workflows

## Purpose

Use this reference to write, check, visualize, run, and resume a Metaflow flow script without relying on repository tutorials.

## Local loop

1. Put the flow class in a Python file and instantiate it under `if __name__ == "__main__"`.
2. Check graph validity:
   ```bash
   USERNAME=${USERNAME:-disco} python flow.py --no-pylint check
   ```
3. Inspect routing:
   ```bash
   python flow.py show
   python flow.py output-dot > flow.dot
   ```
4. Run locally with bounded parallelism:
   ```bash
   USERNAME=${USERNAME:-disco} python flow.py run --max-workers 1
   ```
5. Resume from the last failed run when the graph and code still match the intent:
   ```bash
   python flow.py resume
   python flow.py resume step_name
   ```

## Step rules

- Every normal flow has one start step and one end step.
- Each `@step` ends by calling `self.next(...)` except an end step.
- `self.next(self.a, self.b)` creates branches; a downstream join step accepts `inputs`.
- `self.next(self.worker, foreach="items")` fans out over an artifact named `items`; the foreach task reads `self.input` and `self.index`.
- In joins, use `[task.artifact for task in inputs]` or `self.merge_artifacts(inputs)` when artifacts do not conflict.

## Common CLI options

- Top-level: `--metadata`, `--environment`, `--datastore`, `--datastore-root`, `--with`, `--pylint/--no-pylint`.
- `run` and `resume`: `--tag`, `--max-workers`, `--max-num-splits`, `--max-log-size`, `--run-id-file`, `--namespace`.
- Flow-script version: `python flow.py version`.

## Local decorator examples

```python
from metaflow import FlowSpec, step, retry, timeout, resources, environment

class RobustFlow(FlowSpec):
    @retry(times=2)
    @timeout(minutes=5)
    @resources(cpu=1, memory=2048)
    @environment(vars={"MODE": "local-smoke"})
    @step
    def start(self):
        self.next(self.end)

    @step
    def end(self):
        pass
```

Use remote decorators only with the backend prerequisites in `deployment-orchestration`.
