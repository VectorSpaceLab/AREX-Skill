---
name: "workers"
description: "Use workers for Unstract's Celery and Postgres-backed queue
  workers, worker launchers, queue routing, health ports, and operations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# Workers

Use this sub-skill when the task is about asynchronous processing in Unstract: worker launchers, queue selection, Celery / PG-queue routing, worker health, logging, or operations and recovery.

## Owns

- `workers/run-worker.sh`, `workers/run-worker-docker.sh`, `workers/worker.py`, and the worker subpackages under `workers/`.
- Celery workers such as `api-deployment`, `general`, `file_processing`, `callback`, `notification`, `scheduler`, `log_consumer`, `executor`, and `ide_callback`.
- PG-queue workers: the consumer, the reaper, and the named PG queue roles.
- Worker tests, worker health ports, queue routing, metrics, and operational guidance.

## Excludes

- Backend route families, auth, and hosted MCP internals — use `backend-platform`.
- Full-stack bootstrap and container orchestration — use `platform-deployment`.
- Shared SDK / tool packages and tool protocol docs — use `sdk-and-tools`.
- Frontend runtime config or route changes — use `frontend`.
- Repo test-rig manifests and coverage reporting — use `testing-rig`.

## Start Here

Read `references/worker-matrix.md` first when you need to understand:

- which worker type owns a queue,
- which health port it uses,
- how the Celery set differs from the PG-queue set,
- or how the launcher CLI maps aliases to worker directories.

Read `references/troubleshooting.md` when the issue is a worker that does not start, drains the wrong queue, or fails a health / callback check.

For quick inspection, the usual first command is the launcher help path:

```bash
cd workers
./run-worker.sh --help
```

## Shared References

- `references/worker-matrix.md` — worker aliases, queues, ports, and launch modes.
- `references/troubleshooting.md` — worker startup, queue routing, health, and PG-queue issues.
- `../references/service-map.md` — repo-wide service map and dependencies.
- `../references/installation-and-env.md` — install and environment matrix for worker workflows.
- `../references/repo-provenance.md` — source snapshot used to build this skill.

## Common Task Routing

| User request | Read next |
| --- | --- |
| "Which worker handles this queue?" | `references/worker-matrix.md` |
| "How do I start a specific worker?" | `references/worker-matrix.md` |
| "How does the PG queue consumer or reaper work?" | `references/worker-matrix.md` |
| "Why is a worker not processing tasks?" | `references/troubleshooting.md` |
| "Why is health or metrics failing?" | `references/troubleshooting.md` |

## Safety Boundaries

- Do not assume live RabbitMQ, Redis, or PostgreSQL are available unless the user explicitly wants runtime validation.
- Do not confuse the Celery fleet with the PG-queue fleet; they are intentionally separate launch sets.
- Do not debug queue routing from the wrong worker directory; the launcher aliases and worker packages have their own ownership rules.
