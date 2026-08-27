---
name: service-ops
description: "Guide for the lmms-eval HTTP server, Python clients, MCP tooling,
  TUI/web UI, and job scheduler operations."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# service-ops

Use this route when the user wants to start, inspect, or debug the lmms-eval service layer.
It covers the HTTP server, async clients, queue and job lifecycle, MCP tooling, and the TUI/web UI backend.

## Read first

- `../../references/service-ops.md`
- `../../references/api-reference.md`
- `../../references/troubleshooting.md`

## What this route covers

- `ServerArgs` and the HTTP server launch path.
- `EvalClient` and `AsyncEvalClient` for asynchronous evaluation submission.
- `JobScheduler` queueing, polling, cancellation, and cleanup.
- MCP server/client/tooling behavior.
- TUI and web UI backend discovery and startup.
- Queue pressure, port conflicts, and other long-running service concerns.

## Typical workflow

1. Confirm whether the user needs the HTTP server, the MCP entry point, or the web/TUI backend.
2. Check the service configuration object and the public client signatures in `api-reference.md`.
3. Use the bundled smoke scripts before launching a real job.
4. For async evaluation, submit jobs first and poll them later instead of blocking the training loop.
5. For queue issues, inspect job state transitions and cleanup behavior before changing anything else.

## Helpful commands

```bash
lmms-eval serve --help
lmms-eval mcp --help
lmms-eval ui --help
lmms-eval tui --help
```

## Bundled scripts

- `../../scripts/service_api_smoke.py` — inspect the server, client, MCP, and TUI backend APIs.
- `../../scripts/batch_watchdog.py` — monitor heartbeat files and fail fast on hung distributed jobs.
- `../../scripts/job_scheduler_smoke.py` — smoke the job scheduler lifecycle without submitting real evaluation work.

## Cross-route handoff

- Send one-off eval CLI or Python-library usage to `cli-and-workflows`.
- Send model backend or media decode issues to `model-backends`.
- Send task YAML and request-shape issues to `task-authoring`.

## Common failure modes

- Port conflicts or missing service extras at startup.
- Queued jobs that never transition because the worker is blocked.
- Cancellation requests for jobs that are already running or finished.
- MCP imports that fail because the installed package version is incompatible.
- TUI/web backend startup issues caused by missing UI dependencies.

Use the service smoke scripts to confirm the stack is wired before debugging a live job or client call.
