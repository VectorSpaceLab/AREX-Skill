---
name: runner-and-programmatic
description: "Guides programmatic Metaflow execution with Runner, NBRunner,
  Deployer bridge objects, subprocess status, logs, async waits, and returned
  run/task inspection."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Runner and Programmatic Execution

Use this sub-skill when a task asks to run a Metaflow flow from Python code, automate a local smoke test, inspect `ExecutingRun`/`ExecutingTask`, stream logs, or bridge to deployment objects programmatically.

## Quick Route

- Read [`references/runner-api.md`](references/runner-api.md) for verified `Runner` usage, kwargs placement, returned objects, status, logs, and artifact access.
- Read [`references/notebook-and-spin.md`](references/notebook-and-spin.md) for notebook and Spin-adjacent APIs.
- Read [`references/troubleshooting.md`](references/troubleshooting.md) when subprocesses fail, time out, or return an unexpected `Run` lookup error.
- Run [`scripts/runner_smoke.py`](scripts/runner_smoke.py) for a self-contained local programmatic smoke test.

## Minimal Programmatic Pattern

```python
from metaflow import Runner

with Runner("flow.py", show_output=False, pylint=False, env={"USERNAME": "disco"}) as runner:
    executing = runner.run(max_workers=1)
    print(executing.status, executing.returncode)
    print(executing.run.pathspec)
```

Top-level flow-script options such as `pylint=False`, `profile=...`, `env=...`, or `datastore=...` belong on `Runner(...)`. Run-command options such as `max_workers=1`, `tags=[...]`, or `run_id_file=...` belong on `runner.run(...)`.

## Boundaries

- For writing the flow file itself, route to [`../flow-authoring/SKILL.md`](../flow-authoring/SKILL.md).
- For detailed object traversal after a run exists, route to [`../client-and-data/SKILL.md`](../client-and-data/SKILL.md).
- For real Argo or Step Functions deployment prerequisites, route to [`../deployment-orchestration/SKILL.md`](../deployment-orchestration/SKILL.md).
