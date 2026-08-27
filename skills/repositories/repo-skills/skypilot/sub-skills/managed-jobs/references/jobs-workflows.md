# Managed Jobs Workflows

This reference distills SkyPilot managed-job behavior from the `sky jobs` CLI, `sky.jobs` SDK surface, managed-job docs, job-group docs, examples, and managed-job tests. It is self-contained; do not require future agents to read the original repository checkout.

## Mental Model

- A managed job is submitted with `sky jobs launch`; SkyPilot provisions a temporary cluster or pool worker, runs the task or DAG, monitors it, recovers from infrastructure failures, and cleans resources up when done.
- A managed job may be a single task, a sequential pipeline, or a parallel job group. All use `sky jobs launch`.
- User program logs and controller logs are different. User logs show `setup` and `run`; controller logs show provisioning, scheduling, resource search, preemption, recovery, and cleanup.
- Managed jobs are designed for production scale-out. For interactive SSH/debug sessions, route to the cluster operations sub-skill.
- Managed jobs rely on the SkyPilot API server. Programmatic calls return request IDs and should be paired with `sky.get()` or `sky.stream_and_get()` as appropriate.

## Launch From YAML Or Command

Use a standard SkyPilot task YAML for repeatable jobs:

```bash
sky jobs launch -n train-a100 train.yaml -y
```

Useful launch flags:

- `-n, --name`: managed job name; use stable, non-path names.
- `--infra`, `--gpus`, `--cpus`, `--memory`, `--instance-type`, `--num-nodes`, `--use-spot`: resource overrides shared with task YAML workflows.
- `--job-recovery <strategy>`: override recovery strategy from the CLI.
- `--env`, `--env-file`, `--secret`, `--secret-file`: pass runtime configuration and secrets.
- `-d, --detach-run`: return after submission instead of streaming logs.
- `-p, --pool <pool-name>` with optional `--num-jobs <n>`: submit one or more jobs to an existing jobs pool.
- `--git-url` and `--git-ref`: use a Git source instead of local workdir transfer when appropriate.

Command entrypoints are accepted when the entrypoint is not a YAML path:

```bash
sky jobs launch -n quick-check --cpus 2+ "python -u train.py --epochs 1" -y
```

For long-running workloads, prefer YAML over one-line commands because YAML captures resources, setup, checkpoint mounts, secrets, and recovery policy in one reviewable artifact.

## Queue And Status Triage

List managed jobs:

```bash
sky jobs queue
```

Common filters:

```bash
sky jobs queue --skip-finished
sky jobs queue --status RUNNING,RECOVERING
sky jobs queue --status FAILED,FAILED_SETUP,FAILED_PRECHECKS,FAILED_NO_RESOURCE,FAILED_CONTROLLER
sky jobs queue --since 7d
sky jobs queue --after "2026-01-01" --before "2026-01-31"
sky jobs queue --all
sky jobs queue --limit 100
sky jobs queue --refresh
```

Status meanings to use when diagnosing:

- `PENDING`: waiting for scheduler/controller capacity or resources.
- `STARTING`: provisioning and launching the worker cluster.
- `RUNNING`: user workload is running.
- `RECOVERING`: the worker cluster is being replaced after preemption or infrastructure failure.
- `SUCCEEDED`: user workload completed successfully.
- `CANCELLING` / `CANCELLED`: user requested cancellation and cleanup is in progress or complete.
- `FAILED`: user `run` failed and recovery policy did not retry or retries were exhausted.
- `FAILED_SETUP`: setup failed.
- `FAILED_PRECHECKS`: invalid config, credentials, or prechecks failed; do not expect automatic retry.
- `FAILED_NO_RESOURCE`: resource search exhausted configured retry behavior without finding capacity.
- `FAILED_CONTROLLER`: controller process failed unexpectedly; inspect controller logs and API server/controller health.

`--since` and `--after` are mutually exclusive. A bare `-s` historically meant `--skip-finished`; prefer explicit `--skip-finished` or `--status <STATUS>`.

## Logs And Log Selection

User logs:

```bash
sky jobs logs <job-id>
sky jobs logs <job-id> --no-follow
sky jobs logs <job-id> --no-follow --tail 200
sky jobs logs -n <job-name> --no-follow
```

Controller logs:

```bash
sky jobs logs --controller <job-id> --no-follow
sky jobs logs --controller -n <job-name> --no-follow
```

Task-specific logs for pipelines and job groups:

```bash
sky jobs logs <job-id> 0
sky jobs logs <job-id> train
sky jobs logs -n <job-name> eval --no-follow
```

Download logs:

```bash
sky jobs logs --sync-down <job-id>
sky jobs logs --controller --sync-down <job-id>
```

Rules of thumb:

- Use job ID for terminal jobs; name lookup is most reliable for active nonterminal jobs and may be ambiguous when names are reused.
- Use controller logs for resource search, cloud failures, preemptions, recovery attempts, and setup/provisioning failures.
- Use user logs for application output, setup output, and final exit behavior.
- `--tail` is for streamed/printed logs, not `--sync-down`.

## Cancellation

Cancel by ID, name, pool, or broad scope:

```bash
sky jobs cancel <job-id> -y
sky jobs cancel <job-id-1> <job-id-2> -y
sky jobs cancel -n <job-name> -y
sky jobs cancel --pool <pool-name> -y
sky jobs cancel --all -y
```

Use `--graceful` and optionally `--graceful-timeout <seconds>` when the workload should flush state before being terminated:

```bash
sky jobs cancel <job-id> --graceful --graceful-timeout 300 -y
```

Only one cancellation selector may be used at a time: job IDs, `--name`, `--pool`, `--all`, or `--all-users`.

## Recovery And Checkpointing

Infrastructure failures and spot preemptions are recovered by launching replacement resources. User-code failures are not retried unless configured.

Recommended YAML pattern for transient application failures:

```yaml
resources:
  accelerators: A100:8
  job_recovery:
    max_restarts_on_errors: 3
    recover_on_exit_codes: [33, 34]
```

Guidance:

- Use `resources.use_spot: true` or `sky jobs launch --use-spot` for spot jobs.
- Use `resources.any_of` with both `use_spot: true` and `use_spot: false` for spot-first fallback to on-demand/reserved resources.
- Put checkpoints on persistent storage: Kubernetes volumes for shared filesystems, or cloud bucket mounts for cross-region/cloud recovery.
- Do not include exit code `137` in `recover_on_exit_codes`; SkyPilot uses it internally.
- If a job restarts from scratch after preemption, the missing piece is usually application-level checkpoint save/load, not SkyPilot recovery itself.
- `spot_recovery` is deprecated in favor of `job_recovery`; modern YAML should use `job_recovery`.

Difficult long-running spot training template:

```yaml
name: resilient-train
resources:
  accelerators: A100:8
  any_of:
    - use_spot: true
    - use_spot: false
  job_recovery:
    max_restarts_on_errors: 3
    recover_on_exit_codes: [33, 34]
file_mounts:
  /checkpoint:
    name: <persistent-bucket-or-volume-name>
    mode: MOUNT
run: |
  python train.py \
    --checkpoint-dir /checkpoint \
    --resume
```

Ask the user to fill provider/storage details and route storage specifics to the infrastructure-storage sub-skill.

## Pipelines

A managed pipeline is a multi-document YAML with sequential tasks. Later tasks wait for earlier tasks and are skipped if an earlier task fails.

```yaml
name: train-eval
---
name: train
resources:
  accelerators: A100:8
  any_of:
    - use_spot: true
    - use_spot: false
file_mounts:
  /checkpoint:
    name: <shared-checkpoint-store>
    mode: MOUNT
run: |
  python train.py --checkpoint-dir /checkpoint
---
name: eval
resources:
  accelerators: T4:1
  use_spot: false
file_mounts:
  /checkpoint:
    name: <shared-checkpoint-store>
    mode: MOUNT
run: |
  python eval.py --checkpoint-dir /checkpoint
```

`SKYPILOT_TASK_ID` is unique per task in a managed pipeline and is useful for log correlation.

## Job Groups

Job groups run multiple task documents in parallel under one managed job. Use them for heterogeneous services that need to communicate, such as RL trainer/reward/rollout/replay components.

Minimal job-group YAML:

```yaml
---
name: server-client
execution: parallel
---
name: server
resources:
  cpus: 2
  infra: kubernetes
run: |
  python3 -m http.server 8080
---
name: client
resources:
  cpus: 2
  infra: kubernetes
run: |
  curl http://server-0.${SKYPILOT_JOBGROUP_NAME}:8080/
```

Job-group rules:

- Header must include `execution: parallel`.
- Every task document must have a unique `name`.
- Service discovery hostname format is `{task_name}-{node_index}.{job_group_name}`.
- `SKYPILOT_JOBGROUP_NAME` is injected into tasks.
- Use `primary_tasks` for tasks that define lifecycle completion; tasks not listed are auxiliary.
- Use `termination_delay` as a duration string or per-task dict so auxiliary services can flush before termination.
- Hostname-based service discovery currently requires Kubernetes; on other clouds, tasks may run in parallel but should not rely on this hostname format.
- Use `sky jobs logs <job-id> <task-id-or-name>` to focus logs on a task.

Primary/auxiliary pattern:

```yaml
---
name: train-with-services
execution: parallel
primary_tasks: [trainer]
termination_delay:
  default: 30s
  replay-buffer: 1m
---
name: trainer
run: python train.py
---
name: replay-buffer
run: python replay_buffer.py
```

## Pools

Managed-job pools keep workers warm for workloads with expensive setup or many similar jobs.

Create or update pool config:

```bash
sky jobs pool apply -p <pool-name> pool.yaml -y
sky jobs pool apply -p <pool-name> --workers 5 -y
```

Inspect and tear down:

```bash
sky jobs pool status
sky jobs pool status <pool-name> -v
sky jobs pool logs --controller <pool-name> --no-follow
sky jobs pool logs <pool-name> <worker-id> --no-follow
sky jobs pool logs <pool-name> --sync-down
sky jobs pool down <pool-name> -y
```

Submit jobs to a pool:

```bash
sky jobs launch -p <pool-name> -n <job-name> job.yaml -y -d
sky jobs launch -p <pool-name> --num-jobs 10 -n sweep job.yaml -y -d
```

Important pool caveats:

- When submitting jobs to a pool, setup, file mounts, and storage mounts in the submitted job may be ignored; update the pool with `sky jobs pool apply` instead.
- `--num-jobs` requires `--pool`.
- `pool down` checks for nonterminal jobs and can offer to cancel them first; avoid tearing down a pool while jobs are still needed.
- Pool YAML uses a `pool:` section. Route detailed pool YAML field syntax to task-yaml.

## Python SDK Equivalents

Observed public signatures include:

```python
import sky

request_id = sky.jobs.launch(task_or_dag, name='job-name', pool=None, num_jobs=None)
job_ids, handle = sky.get(request_id)

queue_request = sky.jobs.queue(refresh=False, skip_finished=False, all_users=False, job_ids=None)
records = sky.get(queue_request)

sky.stream_and_get(sky.jobs.cancel(job_ids=[job_ids[0]]))
sky.jobs.tail_logs(job_id=job_ids[0], follow=True, controller=False)
sky.jobs.download_logs(name=None, job_id=job_ids[0], refresh=True, controller=False)

sky.stream_and_get(sky.jobs.pool_apply(task, pool_name='pool-a', workers=None))
sky.stream_and_get(sky.jobs.pool_status(pool_names=None))
sky.stream_and_get(sky.jobs.pool_down(pool_names='pool-a'))
```

For job groups in Python, build a `sky.Dag`, set `dag.name`, call `dag.set_execution(sky.DagExecution.PARALLEL)`, add named `sky.Task` objects, then launch with `sky.jobs.launch(dag)`. For loading a job-group YAML programmatically, use `sky.utils.dag_utils.load_job_group_from_yaml()` in a normal SkyPilot Python environment.

## Native Evidence And Safe Checks

Safe local checks:

```bash
sky jobs --help
sky jobs launch --help
sky jobs queue --help
sky jobs logs --help
sky jobs pool --help
python sub-skills/managed-jobs/scripts/jobs_command_builder.py --help
```

Cloud-bound evidence from native tests should be treated as skip-by-default unless credentials/resources are explicitly authorized: managed-job smoke tests, recovery tests, storage tests, TPU/GPU tests, and real pool creation.
