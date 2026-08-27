---
name: flow-task-authoring
description: "Author, run, debug, and locally test Prefect flows and tasks with
  retries, caching, states, futures, task runners, results, transactions, hooks,
  and concurrency."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Flow And Task Authoring

Use this sub-skill when a task is about writing or debugging Prefect SDK workflow code: `@flow`, `@task`, local execution, state handling, futures, task runners, result persistence, retries, caching, logging, hooks, interactive pauses, transactions, and unit-style tests.

## Start Here

1. Read [references/api-reference.md](references/api-reference.md) for live Prefect 3.6.24 decorator parameters, state constructors, futures, task runners, cache policies, result storage, pause/resume, transactions, and concurrency contexts.
2. Read [references/workflows.md](references/workflows.md) for copyable patterns: basic flows, task composition, `.submit()`, `.map()`, state inspection, local tests, cached tasks, result persistence, retry policies, hooks, and nested subflows.
3. Read [references/troubleshooting.md](references/troubleshooting.md) before diagnosing parameter validation, cache misses, retry behavior, missing logs, unresolved futures, failed states, result persistence, async/sync mismatches, pause/suspend behavior, timeouts, and concurrency-limit failures.
4. Run `python scripts/flow_task_smoke.py --help` when you need a deterministic local smoke example with no network, credentials, long-running service, or original-repo dependency.

## Routing Boundaries

- Use this sub-skill for authoring and local SDK behavior inside Python files, including `Flow` and `Task` objects created by decorators.
- Route deployment creation, `flow.serve`, `flow.deploy`, schedules, work pools, work queues, workers, and `prefect.yaml` to `../deployments-workers/SKILL.md`.
- Route CLI profiles, server startup/status, Cloud login, dashboard, variables, artifacts, and operational commands to `../cli-server-operations/SKILL.md`.
- Route direct `get_client`, `PrefectClient`, schema models, profiles/settings internals, and `temporary_settings` to `../api-client-settings/SKILL.md`.
- Route maintainer-only repository changes, test selection, `uv`/`just`, generated docs, and source-tree development workflow to `../repo-development/SKILL.md`.

## Safe Defaults

- Prefer direct local calls to `flow_fn(...)` or `task_fn(...)` while authoring; add deployments/workers only after the workflow behavior is correct.
- Prefer `@flow(log_prints=True)` or `get_run_logger()` when the user expects logs to appear in Prefect run logs.
- Prefer `.submit()` or `.map()` only inside a flow when concurrency or dependency tracking is needed; call tasks directly when sequential behavior is clearer.
- Prefer `future.result()` or `PrefectFutureList.result()` before returning or asserting values; use `return_state=True` when debugging failed states without raising immediately.
- Prefer explicit `persist_result=True`, `result_storage_key`, or `cache_policy=INPUTS` when cache/result reuse must survive beyond one task call.

## Bundled Script

- `scripts/flow_task_smoke.py` demonstrates deterministic flow/task authoring, local HTML parsing adapted from the repo example without network, retries, cache configuration, futures, mapping, hooks, and state inspection.
- The script prints JSON and supports `--mode basic`, `--mode futures`, `--mode state`, `--mode cache`, and `--mode all` for focused checks.
