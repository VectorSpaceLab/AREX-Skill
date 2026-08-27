# Task Execution Troubleshooting

## Purpose

Use this when task creation, launch, provider dispatch, logs, interactive URLs,
quota, storage, GPU package selection, or multi-node execution behaves
unexpectedly. Start with observable status and job data before changing code.

## Fast Triage Checklist

1. Identify task id, job id, experiment id, provider id/name/type, and whether
   the job is batch, sweep parent/child, or interactive.
2. Read job status and `job_data.launch_progress`.
3. Determine dispatch path: local `WAITING` queue or remote queue/provider.
4. Fetch the right logs:
   - local provider: stdout/stderr machine logs;
   - remote provider: durable provider logs, live provider logs, and request logs;
   - SDK task output: task logs.
5. Check quota hold/usage if minutes were requested.
6. Check provider credentials and `provider.check()` before retrying remote
   launches.
7. For file-not-found errors, confirm file placement mode: manual, uploaded,
   GitHub full, or GitHub subdirectory.

## Common Symptoms

| Symptom | Likely causes | What to inspect | Recovery |
| --- | --- | --- | --- |
| YAML task creation fails | Unknown top-level key, missing `run`, old `env`/`script` naming, unknown provider name | YAML validation detail and provider list | Use canonical fields `envs` and `run`; set `resources.compute_provider` to an exact team provider name or omit it for default provider. |
| Provider not found or disabled | Provider id belongs to another team, provider deleted, provider disabled, interactive import stored no provider by design | Launch request provider id, team id, provider read response | Choose provider at launch; re-enable or recreate provider; do not persist provider id on interactive imports unless launch flow expects it. |
| Job stuck in `WAITING` | Local queue is running another batch job, previous local process has not exited, local queue worker blocked | Existing local jobs, current job `launch_progress`, queue worker logs, local provider status | Do not enqueue more local jobs blindly. Stop/finish the running local job or fix local status polling. Interactive jobs should not block the queue after startup. |
| Job stuck in `LAUNCHING` | Setup installing dependencies, setup command waiting for input, provider launch still provisioning, provider health check slow/failing, remote queue worker not running | `launch_progress.phase`, local stdout/stderr, provider request logs, remote queue row status | Make setup non-interactive; inspect request logs; run provider health check; restart background worker only if it is not polling. |
| Immediate `FAILED` before logs | Provider validation error, missing secrets, disabled provider, malformed `ClusterConfig`, setup exited non-zero before producing output | HTTP error detail, job error message, launch progress, provider check result | Fix secrets/provider config/cluster config first; rerun only after the launch request can be reconstructed. |
| No machine logs | Job still `WAITING`, provider metadata missing, remote durable log not written yet, provider-native job id unknown, local workspace not attached to provider instance | `provider_id`, `cluster_name`, `provider_job_id`, `provider_launch_result`, job status | For local, fetch stdout/stderr. For remote, use `provider_logs?live=true` and request logs. If no provider id or cluster name exists, the launch failed before provider dispatch. |
| `provider_logs.txt` empty or stale | The SDK wrapper only finished partial/durable writes later, command exited before wrapper flush, local provider uses stdout/stderr | Durable provider log file, live logs, `job_data.live_status` | Use live provider logs while launching/running. For local, ignore durable remote log and read stdout/stderr. |
| Setup command fails | Missing package manager, optional GPU package unavailable, `uv`/Python missing on remote, shell command prompts for input, network timeout | Last setup lines in stderr/stdout, provider request logs, remote setup phase | Add non-interactive flags, pin package variants, split install from run, or prebuild provider image. Do not install broad GPU stacks unless required. |
| Run command cannot find files | Uploaded files not mounted, GitHub subdirectory landed as child, remote cwd differs, manual task has no source files | `file_mounts`, task id, GitHub fields, job workdir behavior, logs showing cwd/listing | Use uploaded directory for local files, set `file_mounts: true`, add `cd <subdir>` for GitHub subdir, or reference files under the copied workdir. |
| `tfl-remote-trap` does not update status | Wrapped command missing, SDK not installed remotely, `_TFL_JOB_ID` or experiment env missing, command path differs in sweep/resume flow | `cluster_config.run`, setup includes SDK install, env vars, `job_data.live_status` | Ensure normal launch wraps with `tfl-remote-trap --`; keep sweep/resume paths in sync; verify SDK install and job env injection. |
| Batch job never reaches terminal | Live status absent and provider polling cannot see job, provider empty-job debounce not reached, VM self-termination failed, local process zombie | Status worker logs, provider `list_jobs()`/cluster state, `provider_jobs_seen_once`, process status | Fix provider polling and request logs; for VM-per-job providers, call stop/terminate when safe; for local, check pid/zombie handling. |
| Interactive task never shows URL | Logs do not contain expected URL pattern, wrong `interactive_type`, gallery URL pattern mismatch, service bound to wrong host/port, tunnel not started | `tunnel_info` response, raw logs, `interactive_gallery_id`, `url_patterns`, cached URLs | Update gallery URL patterns or service startup command; for local, emit a `localhost` URL; for remote, emit tunnel URL text the parser recognizes. |
| Interactive task becomes `FAILED` unexpectedly | Server process exited, setup failed, wrapper reported crash, provider cluster went down, user stop was not recorded as `STOPPING` | Local stdout/stderr or remote provider logs, `live_status`, cluster state | Fix the service command to stay alive; distinguish explicit stop from crash; do not auto-mark interactive sessions `COMPLETE`. |
| Quota not released | Hold created but launch failed before conversion, job terminal without end time, user/team identity missing, usage already recorded | `quota_hold_id`, hold status, usage records, start/end time, user email/team id | Release hold for failed pre-launch jobs; run quota backfill for terminal remote jobs; ensure launch stores user/team/start time. |
| Storage probe not found | Worker wrote to different storage root, object-store credentials missing, remote storage URI absent, JuiceFS gateway not started | Probe job logs, storage env vars in job data, storage provider, cloud credential setup | Fix storage env/credentials/gateway; rerun the storage probe before debugging task code. |
| Multi-node ranks wrong | `num_nodes` missing, command not launcher-aware, custom SBATCH flags override task layout, SkyPilot native env assumptions wrong | Generated SLURM script, SkyPilot run prefix, `MASTER_*`, `RANK`, `WORLD_SIZE`, custom flags | Use explicit `srun`/`torchrun`; set `num_nodes`; only override rank vars intentionally; avoid mistaking `--gpus-per-node` for task-layout flags. |
| GPU package mismatch | Local GPU detection selected wrong CPU/CUDA/ROCm index, cloud image lacks drivers, requested accelerator unavailable, optional dependency not installed | Provider GPU detection, `show_gpus()`, setup logs, image id, accelerator string | Use supported accelerator string, proper image/package index, or CPU fallback only when workflow supports it. |
| Cloud credential error | Missing or masked config, expired token, service account lacks role, region/zone invalid, SSH key not registered | Provider `check()` reason, request logs, provider-specific status snapshot | Repair credentials through provider settings; avoid printing secrets; rerun cheap check before launching a paid job. |
| Remote queue row failed | Job data missing `provider_id`, `team_id`, `cluster_name`, or `cluster_config`; serialized config invalid | Remote queue status, job data, `cluster_config` validation errors | Ensure launch service persists cluster config before enqueue; update migrations/schema only if queue table contract changed. |
| New provider field works in normal launch but not sweep/resume | Field added only to primary launch path | Sweep child job data/config, checkpoint resume config, tests | Apply the provider-field checklist in `provider-reference`; add a sweep or resume regression test. |

## Provider-Specific Checks

### Local

- `WAITING` means local queue delay, not provider provisioning.
- Logs should appear early in stdout/stderr once setup starts.
- Setup timeout failures include tails of stdout/stderr.
- If process status polling fails repeatedly, the queue intentionally gives up
  waiting rather than wedging forever; investigate why provider status cannot
  read the per-job workspace/pid.
- Resource fields do not reserve CPU/GPU memory locally; they are metadata for
  display and package-selection hints.

### SLURM

- SSH mode needs reachable login host, user, key, and host-key policy.
- REST mode needs URL/API token and SLURM REST service compatibility.
- Check generated SBATCH script for partition, custom flags, setup, exported
  env, and run command.
- For multi-node, ensure custom flags do not duplicate or suppress task layout
  unintentionally.
- Logs may require `sacct`, `squeue`, or remote file reads depending on mode and
  cluster policies.

### SkyPilot

- The SkyPilot SDK import and API server must both work.
- Launch returns a request id; request logs may be more useful than job logs
  while provisioning.
- Region, zone, Docker image, spot, and file mounts are passed through the
  SkyPilot task/resource model; invalid values can fail before command start.
- Multi-node rank env is prepended; the user run command still must invoke a
  distributed launcher.

### RunPod

- Pod creation may return a server error after creating the pod; lookup by name
  can recover the pod id.
- SSH is required for some log paths and interactive access.
- CPU versus GPU image selection differs; AMD GPU ids require a ROCm image.
- Network volume and disk settings affect where logs and workdir files live.
- RunPod is single-node; do not promise multi-node behavior there.

### Nebius

- Missing project/subnet settings block launch.
- CLI profile/config and service-account credentials are provider-scoped; ensure
  the right provider record is updated.
- If logs say no public IP yet, wait for VM networking before treating logs as
  absent.
- Job submit/list/cancel methods are intentionally not implemented because the
  VM is the job.

### AWS, GCP, Azure, Lambda, Vast.ai, dstack

- AWS: inspect EC2 state, IAM instance-profile setup, AMI selection, security
  group, spot setting, and console output.
- GCP: inspect operation status, instance status, serial output, image family,
  GPU accelerator availability, and SSH firewall.
- Azure: inspect VM instance view, image fallback, GPU driver extension, managed
  identity self-delete role, and VM/NIC/public-IP cleanup.
- Lambda Cloud: inspect instance type capacity by region, file-system region
  pinning, SSH key names, and cloud-init logs.
- Vast.ai: inspect marketplace offer availability, GPU-only requirement,
  instance label, and provider log readiness.
- dstack: inspect run spec, fleet selection, REST API reachability, run status,
  and logs polling; no standalone GPU catalog is expected.

## Safe Recovery Pattern

1. Do not delete task/job directories until logs and `index.json` are captured.
2. Prefer read-only status, logs, provider check, and storage probe first.
3. Retry only after correcting the likely root cause; repeated retries can leak
   cloud resources or consume quota.
4. For VM-per-job providers, stop/terminate leaked resources if the status
   worker cannot do it.
5. For schema/field changes, add regression coverage for normal launch plus at
   least one difficult path: local queue, sweep child, interactive, or resume.
