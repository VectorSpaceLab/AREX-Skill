---
name: framework-runtime
description: "Routes DI-engine task/middleware, Parallel, Supervisor, and modern
  example workflows."
metadata:
  disco-role: operating
  disable-model-invocation: true
license: Apache 2.0
disable-model-invocation: true
---

# Framework runtime

Use this sub-skill for the task/middleware runtime and the modern example
recipes that build on it.
These workflows are more composable than the legacy serial pipeline family and
are the best fit for multi-process message routing.

## Owns

- `ding.framework.task`, `Task`, `Context`, `OnlineRLContext`,
  `OfflineRLContext`, and the task event helpers
- `Parallel.runner` and the `Parallel` message-routing API
- `Supervisor`, `ChildType`, and env/process supervision helpers
- middleware-based example scripts in `ding/example/`
- runtime helpers such as `task.use`, `task.forward`, `task.backward`,
  `task.wait_for`, `task.emit`, and `task.run`

## Does not own

- CLI/config parsing and config compilation; those live in `cli-config`
- Legacy `serial_pipeline` and data-collection helpers; those live in
  `serial-pipelines`
- Env-wrapper shape debugging; those live in `env-integration`

## Read this first when the user asks

- how to write or debug a `task.start(...)` workflow
- how the repo's modern `ding/example/*.py` scripts are structured
- how to use `Parallel.runner` or recover from multi-process routing failures
- how `Supervisor` or `EnvSupervisor` style child management works
- how to build a custom middleware chain for off-policy, on-policy, offline,
  or self-play-style workflows

## Workflow

1. Start with `references/workflows.md` to choose the right runtime shape.
2. Read `references/api-reference.md` for the relevant signatures and routing
   parameters.
3. Use the bundled smoke scripts when you need a small reproducible check that
   the installed environment still supports the task or parallel runtime.
4. Send env-shape or config-shape problems to the neighboring sub-skill rather
   than bloating the runtime section.

## Common decision points

- Use `task.start(async_mode=False)` for the simplest single-process workflow.
- Use `task.start(async_mode=True)` when the runtime must yield and resume
  between middleware steps.
- Use `Parallel.runner` when the recipe needs multiple workers or router-aware
  cross-process messaging.
- Use `Supervisor` when the workflow needs to manage child envs/processes with
  explicit restart/timeout behavior.

## Helpful bundle links

- `references/workflows.md` for the example-family map.
- `references/api-reference.md` for signatures and parameter meanings.
- `references/troubleshooting.md` for process, routing, and message-queue
  failures.
- `scripts/task_smoke.py` and `scripts/parallel_smoke.py` for safe runtime
  checks.
