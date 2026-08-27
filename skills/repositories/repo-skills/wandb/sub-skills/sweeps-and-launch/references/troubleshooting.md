# Sweeps and Launch Troubleshooting

## Sweep config is missing required keys

Symptoms:

- Local validation fails before registration.
- `wandb sweep` rejects the YAML.
- `wandb.sweep` returns backend warnings or errors.

Checks:

- Ensure `method` is present for normal sweeps.
- Ensure `metric` is a mapping with `name`; include `goal` for optimization direction.
- Ensure `parameters` is a non-empty mapping.
- Ensure each parameter spec is a mapping and contains at least one recognized definition key such as `value`, `values`, `min`, `max`, `distribution`, `probabilities`, or nested `parameters`.
- Validate YAML/JSON syntax locally with `python scripts/validate_sweep_config.py sweep.yaml`.

## Sweep runs forever or starts too many trials

Cause: `wandb.agent` and `wandb agent` continue until the sweep completes, is stopped/cancelled, or an explicit count is reached.

Repair:

```bash
wandb agent --count 10 entity/project/sweep_id
```

or:

```python
wandb.agent(sweep_id, function=train, count=10)
```

Do not rely on a nonstandard top-level `count` in the sweep YAML to limit agent execution. Use `wandb sweep --stop`, `--pause`, or `--cancel` for already-running sweeps.

## CLI agent does not shut down child training cleanly

Use the CLI signal-forwarding flag when the training process must receive termination signals:

```bash
wandb agent --forward-signals --count 10 entity/project/sweep_id
```

The SDK signature includes `forward_signals`, but signal forwarding is only supported by the CLI agent. If graceful shutdown matters, prefer the CLI agent or ensure the Python function handles cleanup inside the same process.

## Sweep config has no `program`, or function/program expectations conflict

Symptoms:

- CLI agent receives assignments but cannot launch training.
- A Python agent calls the wrong entry point.
- The training code never reads assigned parameters.

Repair:

- For CLI agents, include `program: train.py` or pass `wandb sweep --program train.py sweep.yaml`.
- For Python agents, pass `function=train` to `wandb.agent` and let that function call `wandb.init()` and read `run.config`.
- Avoid requiring both `program` and `function`; choose the execution model deliberately.

## Launch command cannot choose a backend

Symptoms:

- `wandb launch --queue ...` asks for a resource.
- A queued job waits because no matching Launch agent/resource exists.

Repair:

- Pass `--resource local-process`, `local-container`, `kubernetes`, `sagemaker`, or `gcp-vertex` when queue configuration does not define a resource.
- Confirm the queue exists under the intended entity/project.
- Confirm a Launch agent is watching that queue.

## Launch optional extras or backend packages are missing

Launch backends may require optional dependencies beyond the base W&B package:

- Container/local-container work requires Docker or compatible container tooling.
- Kubernetes work requires Kubernetes client dependencies and a configured cluster context.
- SageMaker work requires AWS SDK dependencies and AWS credentials/permissions.
- Vertex work requires Google Cloud Vertex AI dependencies and GCP credentials/permissions.

If imports fail or backend modules are missing, install the appropriate W&B optional extras or backend SDK packages in the execution environment. Do not add these requirements to the skill runtime content; treat them as user/environment prerequisites.

## Queue/resource mismatch

Symptoms:

- A job is enqueued but never starts.
- A Launch agent starts but rejects jobs.
- Resource args are ignored or reported under the wrong backend.

Checks:

- The job’s `--resource` must match the queue/agent resource configuration.
- `--resource-args` must use the structure expected by that backend.
- For Vertex, use `vertex` or `gcp-vertex` keys and include worker pool specs plus a staging bucket.
- For SageMaker, include a `sagemaker` key with valid training job settings.
- For Kubernetes, provide resource args compatible with the Kubernetes runner and the cluster’s API/permissions.

## Cloud credentials, containers, or cluster access are missing

Do not invent credentials or infrastructure values. Ask the user for the missing entity/project, queue, registry image, cloud account, IAM role, S3/GCS bucket, Kubernetes namespace, service account, or region.

Safe response pattern:

1. Preserve the command shape.
2. Replace unknown infrastructure values with explicit placeholders.
3. State which values the user must provide.
4. Avoid running commands that submit cloud work until the user confirms the target backend and credentials.

## Launch-sweep scheduler errors

`wandb launch-sweep` is experimental and has extra scheduler semantics. If a scheduler job is configured:

- Use `method: custom` for scheduler jobs, or put the W&B optimization method under `scheduler.settings.method` when using the W&B scheduler.
- Ensure `--queue` is supplied or `launch.queue` is present.
- For resume flows, use `--resume_id` with the original queue and compatible scheduler job.
- Do not switch scheduler jobs while resuming an existing launch sweep.

## Bad `--config` or `--resource-args` input

`wandb launch --config` and `--resource-args` accept either a JSON string or a path to a JSON file ending in `.json`. If parsing fails:

- Check shell quoting around inline JSON.
- Prefer a checked-in JSON file for complex nested structures.
- Keep run overrides under `overrides` in `--config`.
- Keep backend-specific settings under `--resource-args`.
- Use `--set-var key=value` for queue template variables rather than mixing them into unrelated JSON.
