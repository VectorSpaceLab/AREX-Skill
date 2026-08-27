# Celery and Background Jobs

This reference covers worker layout, queue ownership, task-writing rules, beat behavior, and restart expectations.

## Worker and queue map

| Worker | Queues | What it should handle |
| --- | --- | --- |
| primary | `celery` | Core coordination, dispatch, cleanup, and lightweight DB-only orchestration. |
| light | `vespa_metadata_sync`, `connector_deletion`, `doc_permissions_upsert`, `checkpoint_cleanup`, `index_attempt_cleanup`, `opensearch_migration` | Fast, short-lived maintenance work. |
| docprocessing | `docprocessing`, `port` | Indexing pipeline work and related port processing. |
| docfetching | `connector_doc_fetching` | Connector fetch work and fetch-side heartbeats. |
| heavy | `connector_pruning`, `connector_doc_permissions_sync`, `connector_external_group_sync`, `csv_generation`, `sandbox` | Slow or resource-intensive external work. |
| monitoring | `monitoring` | Queue health, watchdog, and observability tasks. |
| user_file_processing | `user_file_processing`, `user_file_project_sync`, `user_file_delete`, `user_file_port` | User-uploaded file and project sync work. |
| scheduled_tasks | `scheduled_tasks` | Long-running scheduled-task executor work. |
| beat | scheduler | Periodic schedule generation and tenant-aware dispatch. |

## Task-writing rules

- Use `@shared_task`, not `@celery_app.task`.
- Every enqueue must pass `expires=`.
- Pass `tenant_id` on every tenant-scoped task.
- The task base reads `tenant_id` and sets tenant context before execution.
- Do not rely on Celery soft or hard time limits; the worker pool uses threads, so timeouts must be enforced in the task body.
- Keep long-running execution in dedicated executor tasks and keep dispatcher tasks lightweight.

## Beat and tenancy

- Beat generates tenant-aware schedules and injects tenant IDs for per-tenant work.
- System-wide tasks and per-tenant tasks are different scheduling classes.
- Use queue placement and priority to keep coordination tasks from being blocked by executor work.
- If a task can fall behind without harm, let the expiration drop stale work instead of building an unbounded backlog.

## Development helpers

- The local background-job launcher starts the worker set for development.
- The debugger reload wrapper preserves breakpoints while workers restart.
- Treat both as development-only helpers, not runtime dependencies.

## Operational note

- If you change worker code, ask for a worker restart. There is no automatic hot reload in the running worker fleet.
