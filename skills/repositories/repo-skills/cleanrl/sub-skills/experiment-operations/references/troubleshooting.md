# Experiment Operations Troubleshooting

Use this guide to diagnose operational failures without leaking credentials or accidentally launching long jobs.

## W&B API and Authentication

Symptoms:

- Tracking fails immediately, run metadata cannot be fetched, or resume/reproduce utilities cannot access a run.
- W&B opens a login prompt in a non-interactive environment.
- A command preview includes an API key or `.netrc`-derived secret.

Safe response:

1. Run `sub-skills/experiment-operations/scripts/check_wandb_env.py --require-wandb` and report only set/missing/placeholder status.
2. Confirm whether the user intends online tracking, offline mode, or disabled tracking.
3. For resume, confirm `WANDB_RUN_ID` and `WANDB_RESUME` are set intentionally.
4. Remove keys from transcripts and replace with environment-variable references or redacted placeholders.

## Dry Run Versus Execution

Symptoms:

- User asks for a benchmark or cloud command and the available utility can launch subprocesses, containers, Slurm jobs, or AWS jobs.
- `--workers` is positive or cloud/container flags are present.

Safe response:

- First generate a command matrix or Slurm/Docker preview.
- Verify command count, seed range, environment substitutions, tags, resource settings, and side-effect category.
- Ask for explicit approval before switching from preview to execution.

## Slurm Template Values

Symptoms:

- Submitted job fails before training starts, logs are missing, or array tasks map to wrong seeds/environments.
- Scheduler rejects GPU, CPU, partition, memory, or node settings.

Safe response:

- Recompute `len(env_ids) * num_seeds` and verify the array range.
- Check that `$SLURM_ARRAY_TASK_ID / len_seeds` indexes environments and `% len_seeds` indexes seeds.
- Validate `gpus_per_task * ntasks` before computing CPU-per-GPU.
- Replace cluster-specific partition, node list, exclusions, account, and memory values with user-confirmed values.
- Preview the Slurm script before any `sbatch` call.

## Optuna Reward Scale and Pruners

Symptoms:

- The tuner optimizes one environment while ignoring another.
- Trials prune before learning begins.
- Scores are incomparable across Atari, MuJoCo, classic-control, or custom tasks.

Safe response:

- Require `target_scores` for every environment in multi-environment tuning.
- Use `median` aggregation when outlier environments dominate averages.
- Increase startup trials or disable aggressive pruners for noisy early learning.
- Start with one trial and one seed to validate metric extraction before launching full studies.
- Confirm the TensorBoard metric key exists and contains enough recent values for the averaging window.

## Resume Checkpoint Compatibility

Symptoms:

- Resume starts from step zero, fails to load `agent.pt`, or crashes with state-dict shape mismatches.
- W&B resume creates a new run instead of continuing an existing run.

Safe response:

- Confirm `WANDB_RUN_ID` matches the intended run and `WANDB_RESUME=must` is intentional.
- Check that the script architecture, wrappers, environment id, model dimensions, and hyperparameters match the checkpoint.
- Confirm the checkpoint was saved to the tracked run and not only to a local directory.
- Treat renamed scripts or changed model definitions as incompatible unless the user has a migration plan.

## AWS Credentials and Resources

Symptoms:

- AWS Batch submission fails with credential, region, queue, job definition, image pull, timeout, or resource errors.
- Jobs remain runnable/pending indefinitely.

Safe response:

- Run `sub-skills/experiment-operations/scripts/check_wandb_env.py --require-aws --require-wandb` and resolve missing or placeholder-like settings without printing values.
- Confirm region, job queue, vCPU, memory, GPU count, timeout, retry count, and Docker image accessibility.
- For GPU jobs, verify the queue supports GPU resources and the image runtime is compatible.
- Ask before retrying submissions because retries can create duplicate jobs.

## Docker Image Tags and Builds

Symptoms:

- Image pull fails, container starts without CleanRL scripts, or GPU/video capture fails.
- Multi-architecture builds are unexpectedly slow.

Safe response:

- Prefer immutable image tags for published experiments; use `latest` only for local iteration.
- Confirm build context includes CleanRL scripts and the package metadata needed for installation.
- Check whether the entrypoint starts a virtual display before video capture.
- Ask before `--build`, `--push`, or remote buildx operations.
- For GPU containers, confirm host NVIDIA runtime support and CUDA compatibility.

## Plotting Dependencies

Symptoms:

- Plot scripts fail importing pandas, seaborn, matplotlib, W&B, or LaTeX.
- No curves appear or cached data looks stale.

Safe response:

- Confirm optional plotting dependencies are installed.
- Check W&B project, metric key, selected experiment names, and sample count.
- Clear or regenerate metric-specific caches only after confirming the user does not need them.
- If TeX rendering fails, disable TeX text rendering or use a simpler plot configuration before changing experiment data.
