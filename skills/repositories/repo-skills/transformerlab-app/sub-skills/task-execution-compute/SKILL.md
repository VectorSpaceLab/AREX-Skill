---
name: task-execution-compute
description: "Operate on Transformer Lab task creation, job launch queues,
  compute providers, logs, sweeps, interactive sessions, quota, storage probes,
  and multi-node execution."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# Task Execution And Compute

Use this sub-skill when a request concerns Transformer Lab tasks becoming jobs:
`task.yaml`, task imports, `index.json`, queueing, provider launch behavior,
job states, logs, sweeps, interactive sessions, quota, storage probes, or
multi-node SLURM/SkyPilot execution.

## Read Order

1. Read [task-job-lifecycle](references/task-job-lifecycle.md) for task models,
   launch request construction, queueing, statuses, logs, sweeps, interactive
   sessions, and multi-node behavior.
2. Read [provider-reference](references/provider-reference.md) before changing
   `ClusterConfig`, provider settings, provider-specific launch code, quota,
   storage probes, or cloud/HPC/local provider behavior.
3. Read [troubleshooting](references/troubleshooting.md) for stuck jobs,
   missing logs, tunnel URLs, setup failures, quota holds, provider credentials,
   GPU/backend selection, storage sync, and multi-node rank issues.

## Route Boundaries

- Generic FastAPI router/service/schema style, auth/team dependencies, database
  migrations, and backend test conventions belong in `../backend-api-services/SKILL.md`.
- React task/job screens, polling UI, xterm rendering, and visual verification
  belong in `../frontend-web-app/SKILL.md`.
- `lab` CLI command syntax, Textual job monitor behavior, SDK facade usage, and
  user-facing CLI workflows belong in `../cli-sdk-workflows/SKILL.md`.
- Stay here for the backend semantics that make those surfaces work: task data,
  job data, provider dispatch, status transitions, logs, quota, storage, sweeps,
  interactive sessions, and distributed launch variables.

## Operating Rules

- Treat tasks and jobs as filesystem-backed records. `task.yaml` is the editable
  input; `index.json` is the flat canonical task/job metadata store.
- Treat `ClusterConfig` as the provider-neutral launch contract. When adding a
  field, keep schema parsing, launch request building, job-data persistence,
  provider implementations, and UI/CLI callers in sync.
- Preserve local versus remote dispatch differences: Local jobs enter a
  serialized queue and start as `WAITING`; non-local jobs go through the remote
  queue and provider launch worker.
- Do not assume optional GPU, cloud, SLURM, SkyPilot, RunPod, Nebius, Lambda,
  Vast.ai, or dstack checks were verified unless the current task explicitly ran
  those checks with credentials and hardware.
- Distill or adapt task examples and provider scripts; do not require future
  agents to open original repository docs, scripts, tests, or gallery examples
  to understand the behavior.

## Common Entry Points

- Task creation/import/editing: read `task-job-lifecycle` sections on unified
  creation modes, YAML fields, provider resolution, and file placement.
- Job launch or queue bugs: read `task-job-lifecycle` for launch flow, then
  `provider-reference` for local/remote/provider-specific behavior.
- Job stuck or no logs: start with `troubleshooting`, then inspect job status,
  `job_data.launch_progress`, and the correct log source for the provider.
- Sweeps or interactive tasks: read their dedicated lifecycle sections before
  touching launch or status workers.
- New provider or new provider field: use the provider-field checklist in
  `provider-reference` and the difficult cases below.

## Difficult Usability Cases To Preserve

- Local job stuck with no visible logs: future agents should distinguish
  `WAITING` queue delay from `LAUNCHING` setup delay, avoid starting another
  local job blindly, and know which local machine logs appear before setup,
  during setup, and after the run command starts.
- New provider field across the stack: future agents should update the YAML
  parser, launch request model, `ClusterConfig`, job-data persistence, provider
  implementations, and UI/CLI forms/tests without losing sweep, interactive,
  or resume behavior.
