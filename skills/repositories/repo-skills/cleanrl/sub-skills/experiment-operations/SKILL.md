---
name: experiment-operations
description: "Operate CleanRL experiment matrices, tracking, tuning, resume,
  plotting, container, Slurm, and cloud workflows safely without executing
  long-running jobs or leaking credentials."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Experiment Operations

Use this sub-skill when the task is about CleanRL experiment orchestration rather than changing an algorithm implementation: benchmark command matrices, W&B tracking, Optuna tuning, checkpoint resume, reproduction command recovery, plotting, Docker images, Slurm arrays, or AWS Batch-style submissions.

## Fast Routing

- Generate local benchmark commands or Slurm previews with [references/benchmark-launchers.md](references/benchmark-launchers.md) and the bundled `sub-skills/experiment-operations/scripts/generate_benchmark_commands.py` helper.
- Configure W&B tracking, Optuna tuning, checkpoint resume, reproducibility command recovery, or W&B-based plotting with [references/tuning-and-tracking.md](references/tuning-and-tracking.md).
- Inspect W&B, AWS, and Hugging Face credential readiness without printing secrets with `sub-skills/experiment-operations/scripts/check_wandb_env.py` before any tracked, cloud, or sharing workflow.
- Plan Docker, AWS Batch, Terraform, Slurm, and container image operations with [references/cloud-and-containers.md](references/cloud-and-containers.md); default to dry-run or command preview until the user approves side effects.
- Diagnose operational failures with [references/troubleshooting.md](references/troubleshooting.md) before changing training scripts or credentials.

## Safety Rules

- Do not run long training, Slurm submission, Docker build/push/run, Terraform, or AWS Batch commands unless the user explicitly asks for execution and confirms credentials/resources.
- Do not print API keys, cloud secrets, Hugging Face tokens, full `.netrc` contents, or copied environment values; report only whether required variables are set, missing, or placeholder-like.
- Treat generated benchmark commands as plans. Verify command count, `--env-id`, `--seed`, tracking flags, tags, and resource settings before handing them to execution.
- Keep algorithm-specific hyperparameter meanings and training flags in `training-scripts`; use this sub-skill only to organize how those commands are launched, tracked, tuned, resumed, or plotted.
- Route model artifact evaluation, Hub upload/download, and policy-enjoy workflows to `evaluation-and-sharing`; route contribution or test policy questions to `repo-maintenance`.

## Operational Checklist

1. Identify the operation type: command matrix, tuner, tracking, resume/reproduce, plotting, Slurm, container, or cloud.
2. Decide whether the task is read-only, dry-run, local execution, or external-resource execution; require explicit approval for side-effectful operations.
3. Validate environment readiness with `sub-skills/experiment-operations/scripts/check_wandb_env.py` when W&B, AWS, or Hugging Face credentials may be involved.
4. Generate commands with `sub-skills/experiment-operations/scripts/generate_benchmark_commands.py` or manually mirror its `env_ids × seeds` ordering.
5. Review troubleshooting guidance for the relevant failure mode before modifying credentials, Docker tags, Slurm templates, checkpoint paths, or tuning objectives.
