# Benchmark Launchers

CleanRL's benchmark operation expands one base training command into a deterministic matrix over environments and seeds. The operation is useful for local smoke matrices, tracked benchmark batches, and Slurm array previews. Treat the matrix as a command plan first; execution is a separate user-approved step.

## Command Matrix Semantics

- Inputs are a base `--command`, one or more `--env-ids`, `--num-seeds`, and `--start-seed`.
- Expansion order is seed-major, then environment: for each seed in `start_seed..start_seed + num_seeds - 1`, append every environment.
- Each generated command appends `--env-id <env>` and `--seed <seed>` to the base command.
- If a base command already contains `--env-id` or `--seed`, stop and clarify whether to remove the existing flag; duplicate flags make reproduction ambiguous.
- `--workers 0` in the native benchmark utility is a safe dry-run mode that prints commands without launching subprocesses.
- Positive `--workers` launches local subprocesses when no Slurm template is used, so it can consume CPU/GPU and run for a long time.

Use the bundled helper for safe planning:

```bash
python sub-skills/experiment-operations/scripts/generate_benchmark_commands.py \
  --env-ids CartPole-v1 Acrobot-v1 MountainCar-v0 \
  --command "uv run python cleanrl/ppo.py --no_cuda --track --capture_video" \
  --num-seeds 2 \
  --wandb-tags smoke,planner
```

The expected count is `len(env_ids) * num_seeds`. A three-environment, two-seed request must produce six commands with exactly one `--env-id` and one `--seed` appended to each command.

## Tracking Tags

- W&B tags can be supplied through `WANDB_TAGS` before launch; CleanRL's benchmark utility can also auto-tag with version-control metadata when enabled.
- For deterministic planning, prefer explicit tags such as `--wandb-tags smoke,benchmark,ppo` in the bundled generator.
- Do not use auto-tagging as the only provenance mechanism when the working tree, branch, or PR context matters to the user; record the intended tag set in the handoff.
- Never paste W&B API keys into generated commands. Use environment validation and keep secrets out of command previews.

## Local Worker Guidance

- Classic-control or small CPU jobs can use multiple workers, but set `OMP_NUM_THREADS=1` to reduce thread contention.
- Video capture on headless Linux typically needs a virtual display wrapper such as `xvfb-run -a`; verify this before launching captured-video runs.
- High-throughput vectorized environments, including EnvPool-style or Procgen-style jobs, often achieve better steps-per-second with `--workers 1` because each run already uses substantial parallelism.
- Start with one short command or a dry-run matrix before scheduling all seeds.

## Slurm Preview Pattern

A Slurm array maps `SLURM_ARRAY_TASK_ID` to an environment and seed. The same seed-major order can be represented as:

```bash
env_ids=(CartPole-v1 Acrobot-v1 MountainCar-v0)
seeds=(1 2)
env_id=${env_ids[$SLURM_ARRAY_TASK_ID / 2]}
seed=${seeds[$SLURM_ARRAY_TASK_ID % 2]}
srun uv run python cleanrl/ppo.py --track --env-id "$env_id" --seed "$seed"
```

Before submitting a Slurm job, verify:

- The array range is `0-(command_count - 1)` and the concurrency suffix does not exceed desired simultaneous jobs.
- `gpus_per_task`, `ntasks`, and total CPU settings are internally consistent; CPU-per-GPU is usually `ceil(total_cpus / (gpus_per_task * ntasks))`.
- Log directories, partitions, node exclusions, and node lists are cluster-specific and should not be copied blindly.
- The generated script contains no real credentials and uses the same command reviewed in dry-run form.

The bundled generator can emit a self-contained Slurm preview with `--output-format slurm`; it does not write to `slurm/`, call `sbatch`, or execute training.

## Benchmark Shell Launchers

CleanRL keeps shell launchers for common algorithm families. Treat those launchers as examples of resource shape and command-matrix style, not as runtime dependencies for this skill. When adapting a launcher:

- Extract only the environment list, base command, seed count, worker count, and Slurm resource pattern.
- Re-check algorithm-specific flags with `training-scripts` before using them.
- Convert the launcher into a dry-run matrix first, then request explicit approval for execution.
- Avoid copying stale image tags, cluster partitions, node exclusions, or local queue names into a new environment.
