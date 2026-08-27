# Compute Provider Reference

## Purpose

Read this before changing provider models, launch request fields, provider
settings, provider-specific launch code, quota accounting, storage probes, or
provider tests. It distills the provider abstraction and current provider roles
without requiring links to the original source files.

## Provider Contract

Every compute provider implements a common abstract interface. The most
important method is `launch_cluster(cluster_name, config) -> dict`, where
`config` is a `ClusterConfig` object built by the launch service.

| Method | Expected role |
| --- | --- |
| `launch_cluster(cluster_name, config)` | Provision or select compute and start the task command. Raise exceptions for failures rather than returning success-shaped errors. |
| `stop_cluster(cluster_name)` | Stop, terminate, or submit a stop request for the provider resource. |
| `get_cluster_status(cluster_name)` | Return normalized `ClusterStatus` with `ClusterState` such as `UP`, `DOWN`, `FAILED`, `STOPPED`, `INIT`, or `UNKNOWN`. |
| `list_clusters()` / `get_clusters_detailed()` | List provider resources for UI/status surfaces. |
| `get_cluster_resources(cluster_name)` | Return normalized CPU/GPU/memory/disk details when the provider can report them. |
| `submit_job(cluster_name, job_config)` | Submit to an existing cluster when meaningful; many VM-per-job providers do not support this. |
| `get_job_logs(cluster_name, job_id, tail_lines, follow)` | Fetch machine or provider logs. Prefer point-in-time text when streaming is not implemented. |
| `cancel_job(cluster_name, job_id)` | Cancel a provider-side job or terminate the resource. |
| `list_jobs(cluster_name)` | List provider-side jobs for status polling when the provider has a job queue. |
| `check()` | Return `(healthy, reason)`; remote queue workers call this before launch when available. |
| `show_gpus()` | Return live availability when cheap/reliable, otherwise a catalog or empty list. It should not raise on query failure. |
| `get_request_logs(request_id, tail_lines)` | Optional orchestration logs or status snapshot for launch requests. |

`ClusterConfig` carries these stable provider-neutral fields: identity
(`cluster_name`, `provider_name`, `provider_id`), resources (`instance_type`,
`cpus`, `memory`, `accelerators`, `disk_size`, `num_nodes`), cloud placement
(`cloud`, `region`, `zone`, `use_spot`, `image_id`), execution (`setup`, `run`,
`env_vars`, `file_mounts`), autostop, and provider-specific `provider_config`.

## Provider Resolution And Settings

Provider records are team-scoped. A launch resolves the provider by id, checks
that it belongs to the current team, rejects disabled providers, and instantiates
a concrete provider class from provider type plus stored config.

Common provider config families:

- Shared: `default_env_vars`, `default_entrypoint_run`, `supported_accelerators`,
  `resource_groups`, and `extra_config`.
- SLURM: mode `ssh` or `rest`, endpoint/host/user/key/port, per-user SLURM user,
  per-user SSH key, and per-user/custom SBATCH flags.
- SkyPilot/dstack: server URL, API token, project/default entrypoint, Docker
  image/region/zone overrides.
- RunPod/Vast.ai/Lambda: API key, image/template, region, volume/filesystem, and
  provider-specific marketplace or instance settings.
- AWS/GCP/Azure/Nebius: cloud project/account/team fields, region/zone/location,
  service credentials, subnet/network settings, profile/config names, default
  GPU platform/preset, and resource group details.

Sensitive fields are masked when providers are read back. Do not log API keys,
cloud secrets, service account JSON, SSH private key material, or resolved local
credential files.

## Launch Dispatch Differences

Local provider:

- Job status is `WAITING` until the local queue starts it.
- Queueing is in-memory and serializes execution, not just launch.
- `ClusterConfig.provider_config` includes per-job local workspace metadata.
- `launch_cluster()` starts a detached subprocess; the queue waits for process
  completion for non-interactive jobs.

Non-local providers:

- Normal single-job launch persists a SQL-backed remote queue row as `PENDING`
  and later `DISPATCHED`.
- The remote queue worker reconstructs `ClusterConfig` from job data, checks
  provider health, and calls `launch_cluster()` under a bounded semaphore.
- Sweep children and checkpoint resume construct jobs separately and call the
  provider directly instead of going through the SQL remote queue; keep these
  paths in sync with normal launch.
- Successful launch leaves the job `LAUNCHING` or `INTERACTIVE`; status workers
  advance it via `tfl-remote-trap` live status or provider polling.

## Provider-Specific Roles

### Local

Runs tasks on the API host. It creates a per-job workspace that becomes both the
process `HOME` and cwd, prepares a per-job Python environment from the local
provider base environment, opens `stdout.log` and `stderr.log` before setup,
runs setup with a timeout, and starts the run command as a detached subprocess.
Resource fields are informational for local runs; local machine capacity is the
actual limit.

Key local facts:

- Only one local batch job executes at a time.
- Interactive local jobs skip the queue's completion wait.
- Local setup/package installation uses uv and chooses CPU/CUDA/ROCm package
  indexes from host GPU detection.
- Local logs are stdout/stderr, not durable remote `provider_logs.txt`.
- `stop_cluster()` terminates the process tree by pid; `get_cluster_status()`
  reports `UP` when pid is alive and `DOWN` once it exits.
- Optional sandboxing may isolate the process while still allowing configured
  job, SDK, and cache paths.

### SLURM

Submits jobs to a pre-existing SLURM cluster through SSH or REST. SSH mode can
upload file mounts over SFTP before submission. Launch builds an SBATCH script
with partition, optional custom flags, setup, env vars, distributed defaults,
and the run command.

Key SLURM facts:

- Modes: SSH (`sbatch`, `squeue`/`sacct`, SSH log reads) or REST (`slurmrestd`).
- Custom SBATCH flags may come from user/provider settings or per-run config.
  Per-run flags override user defaults for that job.
- Multi-node jobs add `--nodes`, and default task layout only when custom task
  layout flags are absent.
- Provider status uses cluster/job commands, not a VM lifecycle.
- Provider credentials and user-specific settings are common failure points.

### SkyPilot

Uses the SkyPilot SDK and remote API server. It builds a `sky.Task` from
`ClusterConfig`, sets env vars, setup/run, file mounts, resources, optional
image/region/zone/spot, and `num_nodes`, then submits a launch request. The
launch body uses `down: true` so SkyPilot tears resources down after jobs finish.

Key SkyPilot facts:

- SkyPilot Python package and reachable API server are required.
- `image_id`, `region`, and `zone` may come from provider defaults or per-run
  overrides.
- Multi-node launches prepend distributed env defaults to the run command.
- Request logs are useful because launch returns a request id before the job is
  fully running.
- Empty provider job lists are debounced; for SkyPilot, never seeing any job can
  indicate launch failure rather than success.

### RunPod

Creates a RunPod pod per job. It supports CPU and GPU pods, chooses a default
CPU/CUDA/ROCm image when no image override is provided, configures SSH exposure
for logs, and runs setup plus command through a pod start command that tees
output to a stable run log file and removes the pod after completion.

Key RunPod facts:

- Secure cloud is the default cloud tier unless provider config overrides it.
- Spot/preemptible maps to RunPod interruptible pods.
- Disk space should size both container disk and pod volume when applicable.
- RunPod can return a 5xx after creating a pod; launch recovery looks up a pod
  by name before treating the launch as failed.
- RunPod is single-node in the current implementation.
- SSH/key setup is part of logs and interactive support.

### Nebius

Launches an ephemeral Nebius Compute VM through the Nebius CLI JSON API. It
resolves or creates a subnet, builds cloud-init user data, injects the org SSH
public key, creates a managed boot disk, selects platform/preset/image family,
and starts a VM that runs the task via the SDK status wrapper.

Key Nebius facts:

- Requires team context and either a parent project for automatic network/subnet
  management or an explicit subnet.
- Provider-scoped CLI profile/config and service-account credentials isolate
  multiple Nebius providers for the same team.
- `show_gpus()` is catalog-based from static platform/preset mappings.
- `submit_job()`, `list_jobs()`, and `cancel_job()` are not implemented; the VM
  itself is the job.
- Logs are read over SSH from the instance when it has a public IP.

### AWS

Launches an ephemeral EC2 instance per job. It maps accelerator specs to GPU EC2
instance types or selects CPU instance types from requested CPU/memory, ensures
security group, key pair, and IAM instance profile for self-termination, chooses
an AMI, passes cloud-init user data, supports spot instances, and tags resources
with team and cluster metadata.

Key AWS facts:

- Trainium/Neuron accelerators use Neuron-compatible images rather than NVIDIA
  images.
- IAM instance-profile propagation is retried.
- Logs can come from SSH to the instance and console/request snapshots.
- VM-per-job terminal transitions stop/terminate resources to avoid leaks.

### GCP

Launches an ephemeral Compute Engine VM per job. It maps GPU specs to machine
plus guest accelerator, chooses CPU machine types otherwise, writes a startup
script, ensures SSH firewall rules, supports service account configuration, and
uses spot scheduling when requested.

Key GCP facts:

- GPU launches require suitable images and accelerator zones.
- Startup script handles setup/run and self-termination behavior.
- Request logs may include operation, instance, and serial output.
- Missing instance states are debounced to avoid transient launch races.

### Azure

Launches an ephemeral Azure VM per job. It creates public IP and NIC, assigns a
managed identity, injects SSH public key, uses base64 user data, applies disk
settings, supports spot VMs, configures self-delete RBAC, and installs the GPU
driver extension for GPU VMs.

Key Azure facts:

- VM, NIC, and public IP cleanup order matters.
- GPU driver install can reboot the VM; task runner setup is designed around
  that risk.
- Request logs use VM instance-view status snapshots.
- `ResourceNotFound` may be transient while create/delete propagates.

### Lambda Cloud

Launches an on-demand Lambda Cloud GPU instance. It resolves instance type from
accelerators or provider default, chooses a region with capacity, honors region
constraints from attached file systems, injects SSH key names, passes cloud-init
user data, and self-terminates through the Lambda API on task exit.

Key Lambda facts:

- Capacity is region-specific; file systems pin the launch region.
- Requires at least one SSH key name; team context can provide the org key.
- API key material is used by instance self-termination; treat it as sensitive.
- Logs are read over SSH from the run log path when the instance is reachable.

### Vast.ai

Launches a GPU-only Vast.ai instance from a marketplace offer. It parses
accelerator specs, finds a rentable offer, passes an `onstart` script that runs
setup and command, tees logs, and destroys the instance on exit.

Key Vast.ai facts:

- CPU-only launch is rejected.
- GPU availability is live marketplace-based and may change quickly.
- Log fetching uses provider log/request APIs and may report not-ready while
  the instance starts.
- Missing instances are debounced in status polling.

### dstack

Uses the dstack REST API to apply a run spec. It supports task and dev
environment run types, optional fleet selection, resource specs, spot policy,
merged environment variables, and point-in-time log polling.

Key dstack facts:

- When a fleet is selected, explicit CPU/memory/GPU/disk resources are omitted
  and scheduling targets the fleet.
- `config.run` is expected to already be wrapped by the launch service for
  normal launches; avoid nested wrappers.
- `show_gpus()` returns an empty list because dstack does not expose a cheap
  standalone GPU catalog.
- Logs are fetched through dstack polling rather than streaming follow.

## Quota Holds And Usage

Quota applies when `minutes_requested` is positive:

1. Available quota = total quota minus recorded usage minus currently held
   minutes.
2. Launch rejects when available minutes are insufficient or already overused.
3. A `HELD` quota hold is created before provider dispatch and its id is stored
   in job data.
4. Launch failures release the hold.
5. Terminal remote jobs can convert holds into usage records based on recorded
   start/end times, or release holds for jobs that never entered launch.
6. Use the quota backfill endpoint for completed remote jobs that missed usage
   recording.

When debugging quota, inspect job type, status, `job_data.start_time`,
`job_data.end_time`, `job_data.quota_hold_id`, user/team identity, and whether a
usage record already exists.

## Storage Probes

The storage probe endpoints launch a minimal provider-backed job that runs the
SDK storage probe and writes a sentinel under configured shared storage:

```text
POST /compute_provider/debug/storage-probe?provider_id=<provider_id>
GET /compute_provider/debug/storage-probe/{job_id}
```

Use this only when an authenticated server and selected provider are available.
A failed probe means the worker did not write a sentinel where the controller
expected it; check storage provider env, remote storage URI, object-store
credentials, file mounts, and JuiceFS gateway setup before blaming task code.

## Adding A Provider Field Safely

When adding a field that should affect launch behavior, update all relevant
layers, not just one provider class:

1. `task.yaml` schema resources if users can set it in YAML.
2. Task YAML parser and `index.json` synchronization.
3. Launch request model.
4. Launch service: request merge, secrets/env handling if needed, job-data
   persistence, and `ClusterConfig` construction.
5. Sweep child launch path and checkpoint resume path if the field affects
   repeated launches.
6. `ClusterConfig` model field, default, and serialization.
7. Provider config schemas and provider factory when the field is provider
   setting rather than per-run setting.
8. Each provider that should use or explicitly ignore the field.
9. UI provider/task forms and CLI commands if the field is user-facing.
10. Mocked provider tests and at least one lifecycle test proving job-data and
    cluster-config persistence.

Hard fields to verify are those that affect region/zone/image, spot/preemptible
selection, filesystem mounts, GPU package selection, multi-node layout, or
provider credentials. These often need both mocked unit tests and optional live
provider checks.

## Verification Boundaries

Default repo-skill verification can rely on source inspection and mocked
provider tests. Do not claim live verification for:

- real cloud launches without credentials and cost approval;
- SLURM SSH/REST cluster access;
- SkyPilot server access;
- RunPod/Nebius/Lambda/Vast.ai/dstack account capacity;
- GPU-specific task execution or large gallery installs;
- remote setup shell mutation.

When a user explicitly asks for a live provider check, start with `provider.check()`,
`show_gpus()`, request logs, and a storage probe before running expensive or
long-lived tasks.
