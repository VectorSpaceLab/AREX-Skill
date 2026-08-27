# Worker Matrix

Unstract uses two worker families:

1. The Celery fleet, which handles the traditional queue-based worker types.
2. The PG-queue fleet, which is a separate Postgres-backed consumer / reaper path.

## Celery Worker Set

| Alias | Worker dir | Queue(s) | Health port | Purpose |
| --- | --- | --- | --- | --- |
| `api`, `api-deployment` | `api-deployment` | `celery_api_deployments` | `8080` | API deployment workflows |
| `general` | `general` | `celery` | `8081` | General workflows and webhooks |
| `file`, `file-processing` | `file_processing` | `file_processing,api_file_processing` | `8082` | File-processing flows |
| `callback` | `callback` | `file_processing_callback,api_file_processing_callback` | `8083` | Result aggregation and finalization |
| `log`, `log-consumer`, `logs` | `log_consumer` | `celery_log_task_queue` | `8084` | Log persistence / streaming |
| `notification`, `notify`, `notifications` | `notification` | notification fanout queues | `8085` | Notification delivery |
| `scheduler`, `schedule` | `scheduler` | `scheduler` | `8087` | Scheduled pipeline execution |
| `executor` | `executor` | executor queues | `8088` | LLM extraction / indexing / prompt execution |
| `ide-callback` | `ide_callback` | `ide_callback` | `8089` | Prompt Studio callback flow |

## PG-Queue Set

| Role | Source worker type | Queue(s) | Health port | Purpose |
| --- | --- | --- | --- | --- |
| `pg-queue-consumer` | configurable via `WORKER_PG_QUEUE_CONSUMER_WORKER_TYPE` | configurable via `WORKER_PG_QUEUE_CONSUMER_QUEUE` | `8090` | Generic PG consumer |
| `pg-orchestrator-api` | `api_deployment` | `celery_api_deployments` | set by launcher | API deployment orchestration over PG |
| `pg-orchestrator-general` | `general` | `celery` | set by launcher | General orchestration over PG |
| `pg-fileproc` | `file_processing` | `file_processing,api_file_processing` | set by launcher | File-processing fan-out over PG |
| `pg-callback` | `callback` | `file_processing_callback,api_file_processing_callback` | set by launcher | PG callback role |
| `pg-scheduler` | `scheduler` | `scheduler` | set by launcher | PG scheduler tick |
| `pg-executor` | `executor` | `celery_executor_legacy,celery_executor_agentic,celery_executor_agentic_table` | set by launcher | PG executor RPC |
| `pg-queue-reaper` | n/a | n/a | `8086` | Leader-elected recovery loop |

## Launcher Facts

- `workers/run-worker.sh` is the canonical multi-worker launcher.
- `workers/run-worker-docker.sh` is the Docker-oriented variant.
- `workers/worker.py` is the shared Celery entrypoint.
- `workers/pg_queue_consumer/__main__.py` and `workers/pg_queue_reaper/__main__.py` provide the PG-queue entrypoints.
- The launcher aliases `all` / `celery` and `pg` / `pg-queue` as distinct sets.
- The PG-queue consumer chooses its source worker type before importing the shared worker bootstrap so the correct tasks are registered.

## Operational Clues

- Health endpoints for the Celery workers live on the ports above.
- Metrics for the PG workers are exposed on the health port as `/metrics`.
- The worker docs distinguish Celery-fleet issues from PG-queue issues for a reason; they are different runtime paths.
