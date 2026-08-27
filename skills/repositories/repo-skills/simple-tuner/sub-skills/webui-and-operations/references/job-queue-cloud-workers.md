# Job Queue, Cloud Jobs, and Workers

Use this reference for local GPU-aware queueing, cloud job operations, worker orchestration, and queue governance. Queue and cloud actions can allocate hardware, upload data, incur spend, or interrupt active jobs; get explicit approval first.

## Queue model

Jobs are scheduled by priority, concurrency limits, and FIFO order within a priority tier.

| User level | Default priority | Value |
| --- | --- | --- |
| Admin | Urgent | 30 |
| Lead | High | 20 |
| Researcher | Normal | 10 |
| Viewer | Low | 0 |

Leads/admins may override priority for special cases. Jobs can be `pending`, `queued`, `running`, `completed`, `failed`, `cancelled`, or `blocked` when an approval workflow is required.

## Queue API quick reference

- `GET /api/queue` lists queue entries; filters include status, limit, and whether to include completed jobs.
- `GET /api/queue/stats` reports queue depth, running counts, wait time, concurrency, and local GPU status.
- `GET /api/queue/me` shows the current user's pending/running jobs and best queue position.
- `GET /api/queue/position/{job_id}` reports a specific job's position.
- `POST /api/queue/submit` submits a local or worker-dispatched job.
- `POST /api/queue/{job_id}/cancel` cancels a queued job before it starts.
- `POST /api/queue/{job_id}/approve` and `POST /api/queue/{job_id}/reject` are admin approval actions.
- `GET /api/queue/concurrency` and `POST /api/queue/concurrency` inspect/update limits.
- `POST /api/queue/process` manually triggers scheduling.
- `POST /api/queue/cleanup?days=<n>` removes old terminal entries without touching active jobs.

## Local GPU-aware jobs

Local jobs are submitted through the queue so GPUs are reserved before training starts.

Request fields for `POST /api/queue/submit`:

| Field | Meaning |
| --- | --- |
| `config_name` | Required training environment name. |
| `no_wait` | Reject immediately if required GPUs are unavailable. |
| `any_gpu` | Use any available GPUs instead of configured device IDs. |
| `target` | `auto`, `worker`, or `local`. |
| `worker_labels` | Optional glob-style label requirements when dispatching to workers. |

`GET /api/system/status?include_allocation=true` reports allocated and available GPUs, running local jobs, and per-device allocation. `GET /api/queue/stats` includes local GPU totals and concurrency state.

Local concurrency fields accepted by the concurrency endpoint include:

- `local_gpu_max_concurrent`: maximum GPUs local jobs may occupy; `null` means unlimited.
- `local_job_max_concurrent`: maximum simultaneous local jobs.
- Cloud queue limits such as `max_concurrent`, `user_max_concurrent`, optional team limits, and fair-share scheduling may be updated in the same payload.

Cancellation releases GPUs but intentionally does not auto-start pending jobs during bulk cancellation. Use `POST /api/queue/process` or restart the server after cancellation if pending jobs should resume processing.

## Local jobs CLI

- `simpletuner jobs submit <config-name>` submits with default queue behavior.
- `simpletuner jobs submit <config-name> --no-wait` rejects instead of queueing when GPUs are unavailable.
- `simpletuner jobs submit <config-name> --any-gpu` ignores configured device IDs and uses available GPUs.
- `simpletuner jobs submit <config-name> --target worker|local|auto` chooses dispatch target.
- `simpletuner jobs submit <config-name> --dry-run` previews config, GPU availability, worker pool, queue state, and validation without submitting.
- `simpletuner jobs list` lists recent jobs; `--status`, `--format json`, `--limit`, and `-o field1,field2` narrow output. Dot notation can read nested metadata fields.
- `simpletuner jobs status --format json` returns queue statistics.
- `simpletuner jobs logs <job-id> --follow` streams logs from a job.
- `simpletuner jobs cancel`, `delete`, `retry`, and `purge` manage queued/history entries.
- `simpletuner jobs approval ...` lists, approves, rejects, and inspects approval workflow state.

## Cloud training operations

Cloud training packages local datasets, uploads them to the selected provider after consent, runs training remotely, and tracks status through the same job history/queue surfaces.

Operational rules:

- Always review upload summaries before submission. Local datasets, captions/metadata, and training configuration may be sent to the provider.
- Provider credentials are secrets. Configure them through the UI or CLI secret prompts and never print or store their values in handoffs.
- Sensitive files are excluded during packaging, but do not rely on packaging as a substitute for reviewing dataset folders.
- Replicate-backed uploads are blocked when the packaged archive exceeds the documented size limit.
- Billing starts when remote training begins and stops when it completes or fails. Cost estimates and limits should be checked before approval.
- Cloud jobs are single-shot in this snapshot. There is no built-in DAG/workflow dependency model and no automatic resume from a failed/cancelled remote job.

Cloud CLI patterns:

- `simpletuner cloud jobs submit <config-name> --dry-run` previews a cloud submission without uploading.
- `simpletuner cloud jobs submit <config-name> --provider replicate --hardware-profile <profile>` submits to a provider/hardware target after approval.
- `simpletuner cloud jobs list --status running --format json` lists cloud jobs.
- `simpletuner cloud jobs logs <job-id> --follow` follows provider logs where supported.
- `simpletuner cloud jobs get`, `cancel`, `delete`, and `retry` manage job state/history.
- `simpletuner cloud config show|set-token|delete-token|set` manages provider configuration.
- `simpletuner cloud cost-limit show|set|disable` manages provider spending limits.
- `simpletuner cloud status --format json` checks cloud system/provider health.

## Worker orchestration

Workers let an orchestrator dispatch jobs to remote GPU machines.

1. Start the central server in a mode that includes orchestration APIs.
2. As an admin, create a worker record/token in the WebUI or `POST /api/admin/workers`.
3. Start a worker with `simpletuner worker --orchestrator-url <url> --worker-token <token> --name <name>`.
4. Use `--persistent` for machines that should stay online between jobs; omit it for ephemeral workers that exit after one job.
5. Submit jobs with `target=worker` to require workers, `target=local` for orchestrator GPUs only, or `target=auto` to prefer workers and fall back to local GPUs.

Workers report GPU count, GPU name, VRAM, accelerator type, labels, and heartbeat state. Heartbeats are sent every 30 seconds; workers are marked offline after a timeout window. Orphaned jobs can be requeued when retries remain.

Worker labels support glob-style matching, for example selecting by GPU type, region, team, or lifecycle class. A worker-dispatched job must match label requirements and GPU count and an eligible worker must be idle.

Admin worker operations include:

- `GET /api/admin/workers` to list status and capabilities.
- `POST /api/admin/workers/{id}/drain` to finish current work and prevent new dispatch.
- `POST /api/admin/workers/{id}/token` to rotate a token.
- `DELETE /api/admin/workers/{id}` to remove an offline worker.

## Metrics and queue health

When triaging queue health, collect:

- `GET /api/queue/stats` for global, per-user, local GPU, and worker pool status.
- `GET /api/system/status?include_allocation=true` for GPU allocation details.
- `simpletuner jobs list --format json` or cloud jobs list output for affected job IDs, status, config name, duration, and error message.
- Worker list/status for label, heartbeat, and GPU mismatch issues.
- Approval list/state if jobs are blocked rather than pending.
