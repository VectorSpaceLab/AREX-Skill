# W&B Launch

## What Launch coordinates

W&B Launch packages a runnable job, sends it directly to a resource or queues it for a Launch agent, and tracks the resulting W&B run. Use this reference when the task involves `wandb launch`, `wandb job`, `wandb launch-agent`, queues, or launch sweeps.

Do not use Launch guidance for ordinary `wandb.init()` logging or artifact/model registry operations unless they are part of the job being launched.

## Core command: `wandb launch`

`wandb launch` accepts either a source URI/local path or an existing W&B job:

```bash
wandb launch \
  --uri . \
  --entry-point "python train.py" \
  --entity entity \
  --project project \
  --resource local-process
```

Queue a job instead of running it immediately:

```bash
wandb launch \
  --uri git.example.com/org/repo \
  --entry-point "python train.py" \
  --queue training-queue \
  --entity entity \
  --project project \
  --resource local-container \
  --config '{"overrides": {"args": ["--epochs", "3"]}}'
```

High-value flags:

- `--uri` / `-u`: local path or Git repository URI; creates a job from the source.
- `--job` / `-j`: existing job name such as `entity/project/job-name:version`; does not require `--uri`.
- `--entry-point` / `-E`: entry point within the project; if it looks like a `.py` file, W&B attempts to run it with Python.
- `--build-context`: build context inside source code; compatible with `--uri`.
- `--name`: launched run name.
- `--entity` / `-e` and `--project` / `-p`: destination scope.
- `--resource` / `-r`: execution backend. Supported values are `local-process`, `local-container`, `kubernetes`, `sagemaker`, and `gcp-vertex`.
- `--docker-image` / `-d`: use a specific `name:tag` image.
- `--base-image` / `-B`: base image for job code; incompatible with `--docker-image`.
- `--dockerfile` / `-D`: Dockerfile path relative to the job root.
- `--config` / `-c`: JSON file path or JSON string for Launch config and overrides.
- `--resource-args` / `-R`: JSON file path or JSON string for backend-specific resource args.
- `--set-var` / `-v`: template variable assignments for queues with allow-listing.
- `--queue` / `-q`: queue name; `--queue` without a value uses `default`.
- `--priority` / `-P`: queued job priority: `critical`, `high`, `medium`, or `low`.
- `--async`: run a direct launch asynchronously; it is incompatible with `--queue`.

When pushing to a queue with no resource configuration, provide `--resource` explicitly so W&B knows which backend should execute the job.

## Existing jobs

Use `wandb job` to inspect existing jobs:

```bash
wandb job list --entity entity --project project
wandb job describe entity/project/job-name:latest
```

Create a reusable job from code before launching it repeatedly:

```bash
wandb job create code ./training-code \
  --entry-point "python train.py" \
  --entity entity \
  --project project \
  --name train-job

wandb launch \
  --job entity/project/train-job:latest \
  --queue training-queue \
  --entity entity \
  --project project
```

## Launch agents and queues

A Launch agent watches one or more queues and executes jobs using the queue/resource configuration:

```bash
wandb launch-agent --queue training-queue --entity entity --max-jobs 1
```

Useful agent flags:

- `--queue` / `-q`: queue to watch; repeat it to watch multiple queues.
- `--entity` / `-e`: entity that owns the queues.
- `--max-jobs` / `-j`: maximum jobs to run in parallel; `-1` means no upper limit.
- `--config` / `-c`: agent config YAML.
- `--log-file` / `-l`: internal agent log destination; `-` logs to stdout.
- `--verbose` / `-v`: increase verbosity.

Operational guardrails:

- Keep `--max-jobs` finite unless the user explicitly wants unconstrained parallelism.
- Do not assume the queue’s backend. If the task says “queue this job” but gives no queue configuration, ask for or infer only safe local resources; avoid cloud assumptions.
- Queue names are scoped by entity/project settings and must already exist unless the user has separately created/configured them in W&B.

## Resource selection

### `local-process`

Use for direct local execution without containerization:

```bash
wandb launch --uri . --entry-point "python train.py" --resource local-process
```

Good for quick tests and trusted local code. Do not use it for scheduler jobs that require container execution; Launch scheduler code defaults scheduler jobs away from `local-process`.

### `local-container`

Use when the job should run in a local container:

```bash
wandb launch \
  --uri . \
  --entry-point "python train.py" \
  --resource local-container \
  --docker-image repo/image:tag
```

Choose either `--docker-image` or `--base-image`, not both. Ensure the image has the training dependencies and can access any required data/artifacts.

### `kubernetes`

Use when a Launch agent is running with Kubernetes access and the queue/resource args define the Kubernetes job or custom resource. Resource args are passed as JSON/YAML under a `kubernetes` top-level key or as the Kubernetes object shape expected by the runner.

```bash
wandb launch \
  --uri git.example.com/org/repo \
  --entry-point "python train.py" \
  --queue k8s-queue \
  --resource kubernetes \
  --resource-args k8s-resource.json
```

Kubernetes execution requires a configured cluster context, service account permissions, image pull access, and any namespaces/secrets referenced by resource args. Do not fabricate these values.

### `sagemaker`

Use for AWS SageMaker training jobs when AWS credentials, region, role, output location, and container image/resource args are known:

```bash
wandb launch \
  --job entity/project/train-job:latest \
  --queue sagemaker-queue \
  --resource sagemaker \
  --resource-args sagemaker-resource.json
```

The SageMaker runner expects `resource_args` to include a `sagemaker` section. It resolves AWS session/account details, role ARN, SageMaker training job args, and optional CloudWatch logs. Do not invent IAM roles, S3 paths, subnets, security groups, or registry images.

### `gcp-vertex`

Use for Google Vertex AI custom training jobs when GCP credentials, project, region, staging bucket, and worker pool specs are known:

```bash
wandb launch \
  --job entity/project/train-job:latest \
  --queue vertex-queue \
  --resource gcp-vertex \
  --resource-args vertex-resource.json
```

The Vertex runner accepts resource args under `vertex` or historical `gcp-vertex` keys. It requires:

- `vertex.spec.worker_pool_specs` with at least one worker pool.
- `container_spec` for each worker pool.
- `vertex.spec.staging_bucket`.
- GCP environment credentials that can initialize Vertex AI.

Do not invent project IDs, regions, service accounts, staging buckets, or container registry permissions.

## Launch sweeps

`wandb launch-sweep` runs a sweep whose trials are scheduled through Launch. It is experimental.

```bash
wandb launch-sweep \
  --queue training-queue \
  --entity entity \
  --project project \
  launch-sweep.yaml
```

Useful flags:

- `--queue` / `-q`: queue to push sweep runs to; can also come from the config’s `launch.queue`.
- `--project` / `-p` and `--entity` / `-e`: destination scope.
- `--resume_id` / `-r`: resume by 8-character sweep ID; queue required.
- `--prior_run` / `-R`: attach existing runs.

Launch-sweep config can include normal sweep keys plus `launch` and `scheduler` sections. Scheduler jobs are experimental. If using a scheduler job, prefer `method: custom` or put the optimization method under `scheduler.settings.method` according to the scheduler setup.

## Mapping a local training script to a queued Launch job

When the user asks to queue an existing local script without providing cloud/backend details:

1. Confirm the runnable entry point, for example `python train.py --epochs 3`.
2. Decide whether the source is a local path, Git URI, or pre-created job.
3. Use `local-process` for trusted local direct execution or `local-container` when a local container is available.
4. If queueing, require a real queue name and entity/project; do not assume a cloud queue exists.
5. Put runtime overrides in `--config`, backend-specific settings in `--resource-args`, and queue template values in `--set-var`.
6. Avoid credential/backend assumptions; leave placeholders for user-supplied cloud details rather than inventing them.
