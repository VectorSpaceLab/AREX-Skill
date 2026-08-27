---
name: sweeps-and-launch
description: "Define and run W&B hyperparameter sweeps and W&B Launch jobs,
  queues, agents, and launch sweeps across local process, local container,
  Kubernetes, SageMaker, and Vertex resources."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# W&B Sweeps and Launch

Use this sub-skill when an agent needs to create sweep configs, register sweeps with `wandb.sweep`, run bounded sweep agents with `wandb.agent` or `wandb agent`, or submit W&B Launch jobs/queues/agents. Use other W&B sub-skills for basic `wandb.init` tracking, artifact/model registry I/O, or global CLI setup.

## Route by task

- **Sweep definition and execution:** Read [references/sweeps.md](references/sweeps.md) for config shape, `wandb.sweep`, `wandb.agent`, `wandb sweep`, and `wandb agent` patterns.
- **Launch jobs and queues:** Read [references/launch.md](references/launch.md) for `wandb launch`, `wandb job`, `wandb launch-agent`, `wandb launch-sweep`, resource selection, and queue handoff patterns.
- **Failure repair:** Read [references/troubleshooting.md](references/troubleshooting.md) when configs are rejected, agents run forever, child processes ignore termination, Launch extras/backends are missing, or queue/resource/credential assumptions are unsafe.
- **Offline config linting:** Run `python scripts/validate_sweep_config.py path/to/sweep.yaml` before creating a sweep when you need a safe local check for the required sweep keys and parameter shape.

## Safe defaults

- Prefer bounded sweep agents while iterating: pass `count` to `wandb.agent(...)` or `--count` to `wandb agent` unless the user explicitly wants continuous workers.
- Use exactly one execution style per sweep: either a `program` in the sweep config for CLI agents or a Python `function` passed to `wandb.agent`; do not require both.
- For Launch queues, choose `--resource` deliberately when the queue has no resource configuration: `local-process`, `local-container`, `kubernetes`, `sagemaker`, or `gcp-vertex`.
- Treat cloud Launch examples as templates only. Do not invent credentials, IAM roles, Kubernetes contexts, container registries, S3/GCS buckets, or Vertex project/region values.
