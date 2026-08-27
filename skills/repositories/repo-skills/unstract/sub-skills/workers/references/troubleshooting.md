# Workers Troubleshooting

## Common Symptoms

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| A worker starts but never consumes the expected queue | The launcher alias or `WORKER_TYPE` selected the wrong worker directory | Check the worker matrix and the launcher alias in `run-worker.sh` |
| A PG-queue consumer loads the wrong tasks | `WORKER_PG_QUEUE_CONSUMER_WORKER_TYPE` was not set before import time | Set the source worker type before importing the shared worker bootstrap |
| Health port is open but work is not happening | The worker is healthy at the process level but the queue or backend contract is wrong | Check the queue name, internal API URL, and worker-specific env vars |
| Logs show `plugins` import weirdness | The backend and worker path order is wrong | Make sure the backend source root is ahead of worker paths when composing `sys.path` |
| The reaper is not recovering stranded work | The lease / interval / health settings are misaligned or the required infra is not reachable | Inspect the PG-queue reaper env contract and the Postgres connection |

## Worker-Specific Pitfalls

- The Celery fleet and the PG-queue fleet are independent launch sets. Starting one does not imply the other.
- `workers/run-worker.sh` has many aliases; use the canonical worker names in troubleshooting notes to avoid ambiguity.
- The PG-queue consumer is not a generic Celery worker. It imports a source worker's tasks on purpose, which means the import order matters.
- The log consumer and notification worker families have their own queue and health contracts; do not debug them as if they were the general worker.

## What To Check First

1. Confirm the worker alias, worker directory, and queue mapping.
2. Confirm the internal API and broker env values.
3. Confirm the health port and whether the process is the Celery fleet or the PG fleet.
4. Confirm that the backend import path is not shadowed by the worker tree.
