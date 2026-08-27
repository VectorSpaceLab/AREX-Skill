# Task And Job Lifecycle

## Purpose

Read this when a change touches task creation, `task.yaml`, `index.json`, job
launching, queueing, status transitions, logs, sweeps, interactive sessions, or
multi-node task execution. This reference is distilled from the repository's
own task-execution docs, task/job routers and services, provider queues, SDK
status wrapper, and mocked provider tests. It is self-contained; do not rely on
opening the original docs or scripts for the operating facts below.

## Unified Task Creation Modes

Transformer Lab creates tasks through a unified create endpoint. The create path
normalizes every source into a flat task metadata record and, when available, a
human-editable `task.yaml`.

| Mode | Input | Important behavior |
| --- | --- | --- |
| Blank template | JSON body with `source: blank` | Creates a default remote task and writes a minimal editable YAML template. The team default provider is resolved if available. |
| Directory/ZIP upload | Multipart directory ZIP, assembled upload, or local/team-gallery directory | Finds `task.yaml`, parses it, creates the task, copies the task directory into task storage, and sets `file_mounts: true`. |
| GitHub/gallery import | Gallery entry or JSON GitHub fields | Fetches or synthesizes `task.yaml`, stores GitHub repo/dir/branch fields, and resolves provider for non-interactive tasks. |
| Interactive import | Interactive gallery entry, local template, or GitHub-backed interactive task | Sets `subtype: interactive`, records `interactive_type` and `interactive_gallery_id`, and intentionally clears stored provider selection so the provider is chosen at launch. |
| Team gallery export/import | Existing task exported into team-specific gallery metadata and directory snapshot | Preserves metadata plus task files so a task can round-trip without relying only on GitHub. |

Provider resolution is exact name matching within the current team, ignoring
case and surrounding whitespace. If `resources.compute_provider` names an
unknown provider, the API rejects the YAML and reports available names. If no
provider is named, the team default provider is used, falling back to the first
provider when no default is marked. Interactive imports defer provider choice to
launch time.

## `task.yaml` Shape

The canonical YAML schema is strict about top-level keys: unknown fields are
rejected. The modern names are `envs` and `run`; older examples may use nearby
terms, but the backend parser expects this shape:

```yaml
name: my-training-task
resources:
  compute_provider: Local
  cpus: 2
  memory: 4
  disk_space: 10
  accelerators: "NVIDIA"
  num_nodes: 1
  fleet_name: optional-dstack-fleet
  instance_type: optional-cloud-instance
  cloud: optional-skypilot-cloud
  region: optional-region
  zone: optional-zone
  use_spot: false
  image_id: optional-image-or-docker-reference
envs:
  LEARNING_RATE: "0.001"
setup: |
  pip install -r requirements.txt
run: |
  python train.py
github_repo_url: https://github.com/org/repo
github_repo_dir: subdir
github_repo_branch: main
parameters:
  learning_rate: 0.001
sweeps:
  sweep_config:
    learning_rate: [0.001, 0.01]
  sweep_metric: eval/loss
  lower_is_better: true
minutes_requested: 60
```

Important parser facts:

- `name` and `run` are required.
- Numeric resource values may arrive as numbers or strings; internal metadata
  stores many resource values as strings and `num_nodes` as an integer.
- `resources.compute_provider` becomes `provider_name`; it is resolved to
  `provider_id` before storage for normal tasks.
- `resources.fleet_name` is stored inside a generic per-run config for dstack
  scheduling.
- `envs` becomes `env_vars` in task/job metadata.
- `sweeps` enables `run_sweeps` and stores `sweep_config`, `sweep_metric`, and
  `lower_is_better`.
- `minutes_requested` drives quota hold/usage tracking when present and positive.

When the YAML editor saves through the YAML update endpoint, the API reparses
YAML, resolves provider again when needed, preserves system-owned metadata, and
keeps existing `file_mounts` when the YAML omits that field.

## Task And Job Filesystem Layout

Tasks and jobs are filesystem-backed so cluster nodes can share state through
configured storage. Use placeholders rather than hard-coded local paths:

```text
<workspace>/
  task/ or experiments/<experiment_id>/tasks/
    <task_id>/
      index.json        # flat task metadata
      task.yaml         # editable YAML, when present
      ...task files...  # uploaded/local/team-gallery files
  jobs/
    <job_id>/
      index.json        # job metadata with status, progress, job_data
      stdout.log        # local provider stdout/setup/run output
      stderr.log        # local provider stderr/setup/run output
      pid               # local provider process id
      provider_logs.txt # combined output written by tfl-remote-trap for remote-style runs
  uploads/task/
    <task_id>/...       # uploaded task ZIP assemblies, when used
  team_specific_tasks.json
```

Task `index.json` is flat, not nested under `config`. Common task fields include:

- identity: `id`, `name`, `experiment_id`, `created_at`, `updated_at`;
- execution: `type`, `plugin`, `setup`, `run`, legacy `command`;
- interactive metadata: `subtype`, `interactive_type`, `interactive_gallery_id`;
- provider/resource metadata: `provider_id`, `provider_name`, `cluster_name`,
  `cpus`, `memory`, `disk_space`, `accelerators`, `num_nodes`;
- inputs: `env_vars`, `parameters`, `file_mounts`, GitHub repo/dir/branch;
- sweeps: `run_sweeps`, `sweep_config`, `sweep_metric`, `lower_is_better`.

## File Placement At Runtime

Task files reach the launched process through two mechanisms:

- Uploaded/team-gallery task directories are copied into task storage and mark
  `file_mounts: true`. Launch copies task files into the job directory; local
  launches copy them into the per-job home/cwd, while non-local providers call
  SDK file-mount copying during setup.
- GitHub-backed tasks inject clone setup from `github_repo_url`, optional
  `github_repo_dir`, and optional `github_repo_branch`. A subdirectory import
  may land as a child directory rather than as the current directory root; the
  task's `run` command should `cd` or reference that child explicitly.

The task-placement probe script was left reference-only because it needs an
authenticated CLI, running API server, selected provider, and often network. Its
distilled scenarios are:

1. Manual task: only `task.yaml` and inline `run`; expect no uploaded source
   files beyond the task metadata.
2. GitHub full repo: clone repo contents before `run`; expect repo files in the
   job work area.
3. GitHub subdir: sparse-checkout subdirectory is present as a child; `run`
   must address the child directory.
4. Uploaded directory: `task.yaml` plus task files such as `main.py` are present
   at the work area root.
5. Uploaded current directory: equivalent to uploading the directory path; task
   files remain at the work area root.

## Launch Endpoint And Request Model

Launching a task creates a job and a provider-neutral `ClusterConfig`. The
primary launch endpoint is:

```text
POST /compute_provider/{provider_id}/template/launch
```

The launch request carries:

- task context: `experiment_id`, optional `task_id`, `task_name`, description;
- execution: `run`, optional `setup`, `env_vars`, `parameters`, per-run `config`;
- resources: `cpus`, `memory`, `disk_space`, `accelerators`, `num_nodes`;
- routing: `provider_id`, optional `provider_name`, optional `cluster_name`;
- source files: `file_mounts`, GitHub repo/dir/branch;
- sweeps: `run_sweeps`, `sweep_config`, `sweep_metric`, `lower_is_better`;
- interactive: `subtype`, `interactive_type`, `interactive_gallery_id`, `local`;
- accounting/instrumentation: `minutes_requested`, Trackio and profiling flags.

`ClusterConfig` is the provider-neutral launch object. Its verified fields
include `cluster_name`, `provider_name`, `provider_id`, `instance_type`, `cpus`,
`memory`, `accelerators`, `disk_size`, `num_nodes`, `cloud`, `region`, `zone`,
`use_spot`, `image_id`, `idle_minutes_to_autostop`, `run`, `setup`, `env_vars`,
`file_mounts`, and `provider_config`.

Normal single-job launch flow:

1. Load team and user secrets and reject missing placeholders before launch.
2. Fetch and validate the provider record; disabled providers cannot launch.
3. Check and hold quota when `minutes_requested` is positive.
4. Create a filesystem job with initial status:
   - local provider: `WAITING`;
   - non-local batch: `LAUNCHING`;
   - non-local interactive: `INTERACTIVE`.
5. Build a sanitized cluster name from task/provider name plus a short job id.
6. Merge task env vars, secrets, storage env, job identifiers, Trackio/profiling
   env, file-mount setup, GitHub setup, remote SDK install, and optional cloud
   credential setup.
7. Apply provider-level setup/run hooks when configured.
8. For non-local file mounts, prefix the run command with a `cd` into the copied
   workdir so bare `python main.py` resolves task files.
9. Wrap the final command with `tfl-remote-trap -- <quoted command>` for normal
   single launches.
10. Persist `job_data` and the serialized `cluster_config` into the job record.
11. Dispatch to the local queue or the remote queue.

## Job Metadata And Launch Progress

Job `index.json` stores top-level status plus `job_data`. Common fields:

```json
{
  "id": "job-id",
  "experiment_id": "experiment-id",
  "type": "REMOTE",
  "status": "LAUNCHING",
  "progress": 0,
  "job_data": {
    "task_name": "...",
    "run": "python train.py",
    "setup": "pip install ...",
    "cluster_name": "...",
    "provider_id": "...",
    "provider_type": "local",
    "provider_name": "Local",
    "cpus": "2",
    "memory": "4",
    "accelerators": "NVIDIA",
    "num_nodes": 1,
    "env_vars": {},
    "parameters": {},
    "live_status": "Remote command started",
    "quota_hold_id": "optional-hold-id",
    "cluster_config": {},
    "launch_progress": {
      "phase": "launching_cluster",
      "percent": 70,
      "message": "Launching cluster",
      "steps": []
    }
  }
}
```

Launch progress phases are stored under `job_data.launch_progress`; typical
phases are quota checking, config building, queued, launching cluster, cluster
started/running, and failed. Use this field before guessing why a job is stuck.

## Local Queue Behavior

Local provider launches are serialized. A local launch request returns quickly
with job status `WAITING`, then `enqueue_local_launch()` either starts the job
immediately or places it in an in-memory queue.

Local queue invariants:

- Only one local job launch/execution runs at a time.
- The worker transitions `WAITING` to `LAUNCHING` for batch jobs or
  `INTERACTIVE` for interactive sessions.
- `launch_cluster()` creates the per-job environment and starts a detached
  process, then returns once the process starts.
- For batch jobs, the queue worker waits until the process exits or the job
  reaches a terminal status before draining the next local item. Interactive
  jobs skip this completion wait so long-lived servers do not block the queue.
- The poll interval for local completion is controlled by a local job poll
  environment setting; use it only for tuning, not as a correctness fix.
- Quota holds are released if local provider lookup or launch fails before a
  normal terminal usage record can be produced.

## Remote Direct And Queued Behavior

Normal non-local single-job launches are persisted into a SQL-backed `REMOTE`
job queue and processed by a background worker. The job record must already
contain `provider_id`, `team_id`, `cluster_name`, `created_by_user_id`, and
serialized `cluster_config`; otherwise the worker marks the queue entry and job
failed.

Not every remote-looking path uses that SQL queue. Sweep child launches run in a
background coroutine that calls the provider instance directly for each child,
and checkpoint resume also constructs a new job then calls the provider directly.
When changing launch semantics, update queued, direct sweep, and direct resume
paths together.

Remote queue invariants:

- Queue rows start `PENDING`, become `DISPATCHED`, and are processed FIFO by a
  background worker.
- Launch tasks run concurrently but are capped by a remote-launch semaphore.
- Provider health is checked before `launch_cluster()` when a provider supports
  `check()`.
- A provider error dict or exception becomes job `FAILED`, with launch progress
  phase `failed` and quota hold release.
- Successful provider launch persists provider launch results and request ids;
  the job remains `LAUNCHING` or `INTERACTIVE` until status polling or
  `tfl-remote-trap` advances it.

## Statuses And Terminal States

Canonical job statuses:

| Status | Meaning |
| --- | --- |
| `NOT_STARTED` | Created but not queued. |
| `QUEUED` | Submitted and waiting for provider dispatch. |
| `WAITING` | In the local provider queue. |
| `LAUNCHING` | Provider setup/cluster launch or setup script is running. |
| `INTERACTIVE` | Interactive server/session is active or being kept active. |
| `RUNNING` | The wrapped command has started. |
| `STOPPING` | User requested stop; provider shutdown is in progress. |
| `COMPLETE` | Batch command completed successfully. |
| `STOPPED` | Stopped by user or cancellation path. |
| `FAILED` | Setup, launch, provider, or run command failed. |
| `CANCELLED` | Cancelled before normal execution. |
| `DELETED` | Removed. |
| `UNAUTHORIZED` | Rejected by permission/quota flow. |
| `CREATED` / `STARTED` | Legacy/compatibility statuses; do not introduce new flows with them. |

Terminal statuses are `COMPLETE`, `STOPPED`, `FAILED`, `CANCELLED`, `DELETED`,
and `UNAUTHORIZED`.

Status advancement uses two paths:

- `tfl-remote-trap` writes `job_data.live_status` and updates status to
  `RUNNING` when the wrapped command begins. On successful exit it writes
  `Remote command finished`; on failure it writes `Remote command crashed` and
  marks failure. The status worker fast-path converts these live statuses into
  `COMPLETE` or `FAILED` for batch jobs. Interactive sessions are not auto-marked
  `COMPLETE` just because the wrapper finished.
- Provider polling checks cluster/job state when live status is absent or not
  terminal. VM-per-job providers may be stopped/deleted on terminal transition
  to avoid leaking instances. Shared-cluster providers rely on provider job
  listing where available.

## Logs And Log Endpoints

| Surface | Where content comes from | Notes |
| --- | --- | --- |
| Local machine logs | `stdout.log` and `stderr.log` in the local provider job directory | Files are opened before setup, so setup output can be visible while packages install. |
| Remote durable logs | `provider_logs.txt` in the job directory | Written/overwritten by `tfl-remote-trap`; may only be complete after command exit, though the wrapper flushes periodically. |
| Provider-native logs | Provider `get_job_logs()` or RunPod/Nebius/AWS/GCP/Azure/Lambda/Vast.ai/dstack-specific log readers | Use when durable logs are absent or `live=true` is requested. |
| Request/orchestration logs | Provider request id via `get_request_logs()` | Useful for launch failures before the task command starts. |
| Task SDK output | Task log endpoints and SDK logging files | Separate from machine/provider logs; route CLI/SDK syntax to the CLI/SDK sub-skill. |

Important endpoints:

```text
GET /experiment/{experiment_id}/jobs/{job_id}/provider_logs
GET /experiment/{experiment_id}/jobs/{job_id}/provider_logs?live=true
GET /experiment/{experiment_id}/jobs/{job_id}/request_logs
GET /experiment/{experiment_id}/jobs/{job_id}/task_logs
GET /compute_provider/jobs/{job_id}/check-status?experiment_id=<experiment_id>
```

For local providers, `provider_logs` falls back to stdout/stderr because
`provider_logs.txt` may be empty or stale. For remote providers, `provider_logs`
first reads durable `provider_logs.txt` unless `live=true` is requested.

## Sweeps

Sweeps create one parent `SWEEP` job plus child `REMOTE` jobs for every
cartesian product of sweep parameters.

Sweep launch flow:

1. Launch request has `run_sweeps: true` and non-empty `sweep_config`.
2. Parent job is created immediately with type `SWEEP`, status `RUNNING`, and
   `job_data.sweep_parent: true`.
3. Child launch runs in the background. For each parameter combination, it
   creates a `REMOTE` child job with `sweep_run_index`, `sweep_total`,
   `sweep_params`, and `parent_sweep_job_id`.
4. Parent fields track `sweep_total`, `sweep_completed`, `sweep_running`,
   `sweep_failed`, `sweep_queued`, `sweep_progress`, and `sweep_job_ids`.
5. The sweep status worker periodically reads child jobs, recomputes counts,
   and marks the parent `COMPLETE` when completed plus failed equals total.
6. Sweep result aggregation reads each child `score` or `completion_details`,
   selects the best metric according to `lower_is_better`, and stores
   `sweep_results` on the parent.

When changing launch behavior, keep the normal single-job launch path and the
sweep child path in sync. In particular, verify how `run`, setup, env vars,
file mounts, Trackio/profiling, storage env, provider-specific fields,
`tfl-remote-trap`, and quota behavior apply to sweep children.

## Interactive Tasks

Interactive tasks are long-lived services such as VS Code, Jupyter, SSH, vLLM,
Ollama, or custom templates.

Interactive launch differences:

- Task metadata has `subtype: interactive`, `interactive_type`, and
  `interactive_gallery_id`.
- Provider selection usually happens at launch, not import.
- Initial status is `INTERACTIVE` for non-local providers and `WAITING` for
  local providers until the local queue starts it.
- Interactive setup/run may be resolved from the interactive gallery entry,
  with local versus remote command variants.
- SSH access may inject the organization public key; RunPod also configures SSH
  so machine logs can be fetched.
- Interactive jobs are not automatically marked `COMPLETE`; if the session dies
  unexpectedly it is treated as a failure unless the user requested stop.

Tunnel discovery endpoint:

```text
GET /experiment/{experiment_id}/jobs/{job_id}/tunnel_info
```

Tunnel info reads `interactive_gallery_id`, `interactive_type`, expected URL
patterns, and provider logs. It caches successful URL extraction in job data as
`tunnel_info_urls`/`cached_tunnel_info` so later requests do not depend on log
retention. Local providers read full local logs for tunnel parsing because early
local URLs may scroll out of a short tail.

## Multi-Node SLURM And SkyPilot

Set `resources.num_nodes` in `task.yaml` to request more than one node. The
system does not rewrite your training launcher; `run` must explicitly use the
right distributed entry point, such as `srun`, `torchrun`, or `mpirun`.

SLURM multi-node behavior:

- Adds `#SBATCH --nodes=<num_nodes>`.
- Adds default `#SBATCH --ntasks=<num_nodes>` and
  `#SBATCH --ntasks-per-node=1` only when custom flags do not already set task
  layout. A GPU flag such as `--gpus-per-node` must not suppress these defaults.
- Exports defaults without overwriting user-provided values:
  `MASTER_ADDR`, `MASTER_PORT`, `NODE_RANK`, `RANK`, `LOCAL_RANK`, and
  `WORLD_SIZE`.

SkyPilot multi-node behavior:

- Sets `task.num_nodes` when `num_nodes > 1`.
- Prepends a portable distributed env bootstrap to the run command:
  `MASTER_ADDR`, `MASTER_PORT`, `NODE_RANK`, `RANK`, `LOCAL_RANK`, and
  `WORLD_SIZE` from SkyPilot native env such as `SKYPILOT_NODE_IPS`,
  `SKYPILOT_NODE_RANK`, `SKYPILOT_NUM_NODES`, and GPU-per-node count.

RunPod is single-node in the current implementation. VM-per-job cloud providers
also launch one VM per job unless explicitly extended.

## Reference-Only Source Material

These source materials informed the reference but should not be run by default
from this skill:

- Task placement probe: useful for authenticated, end-to-end placement checks,
  but requires a running server, logged-in CLI, selected provider, network for
  GitHub scenarios, and job wait time.
- Remote setup shell script: documents remote bootstrap steps such as OS tools,
  Python, uv, SDK install, GitHub clone, file mounts, credentials, and SSH keys,
  but it mutates remote systems and should remain reference-only.
- Gallery task examples: useful for valid task shapes and launch patterns, but
  many require network, GPU, model downloads, or large installs and are not
  default verification fixtures.
