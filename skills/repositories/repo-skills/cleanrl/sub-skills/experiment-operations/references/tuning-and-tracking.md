# Tuning, Tracking, Resume, and Plotting

This reference covers CleanRL operations that coordinate experiments after the base training script and algorithm flags have been chosen.

## W&B Tracking

Most CleanRL training scripts expose a `--track` flag and optional video capture through `--capture_video`. When tracking is enabled, runs log metrics, config, and optionally rendered videos to W&B.

Safe tracking flow:

1. Confirm the base command is short enough or explicitly approved for full training.
2. Run `sub-skills/experiment-operations/scripts/check_wandb_env.py --require-wandb` to check that W&B credentials or offline mode are intentional without printing secrets.
3. Use explicit `WANDB_TAGS` for benchmark provenance when comparing versions, command families, or smoke/full runs.
4. Keep `--capture_video` only when rendering dependencies and display support are available.
5. Record the W&B project, entity/team if used, run id, tags, and command plan in the handoff without exposing keys.

Useful environment variables include `WANDB_API_KEY`, `WANDB_PROJECT`, `WANDB_ENTITY`, `WANDB_TAGS`, `WANDB_RUN_ID`, `WANDB_RESUME`, `WANDB_MODE`, and `WANDB_DISABLED`. Values should not be printed.

## Hyperparameter Tuning

CleanRL's `Tuner` wraps Optuna around a training script. It samples hyperparameters, runs the script across environments and seeds, reads TensorBoard scalar metrics, normalizes scores when target ranges are provided, and optimizes the aggregated result.

Core fields:

- `script`: training script path to execute with generated CLI args.
- `metric`: TensorBoard scalar key such as `charts/episodic_return`.
- `metric_last_n_average_window`: number of recent scalar values to average for scoring.
- `target_scores`: mapping of environment id to `[low, high]` score range or `None` for a single environment.
- `params_fn`: Optuna trial callback that returns CleanRL CLI flag names and values.
- `direction`: usually `maximize` for return metrics.
- `aggregation_type`: `average`, `median`, `max`, or `min` over normalized environment scores.
- `sampler` and `pruner`: Optuna components such as TPE samplers and median pruners.
- `storage` and `study_name`: persistent study database settings, defaulting to a local SQLite database.
- `wandb_kwargs`: optional W&B tracking for each tuning trial.

Reward-scale guardrails:

- For multi-environment tuning, provide `target_scores` for every environment; otherwise the largest reward scale can dominate.
- `target_scores=None` is appropriate only for a single environment or when the raw metric scale is intentionally optimized.
- Median aggregation can reduce sensitivity to a single outlier environment; average aggregation rewards broad improvement.
- Pruners are useful but can prune good configurations too early when `num_seeds` is small or early learning is noisy.

Operational guardrails:

- Start with one trial and one seed for smoke validation before launching a full study.
- Use a distinct `study_name` for comparable runs and a persistent storage URI when resuming or distributing tuning.
- Confirm optional dependencies such as Optuna, TensorBoard event reading, W&B, and plotting libraries are installed before starting.
- Keep algorithm-specific search ranges in `training-scripts`; this sub-skill owns tuning orchestration and failure diagnosis.

## Resume Training

CleanRL resume workflows usually combine model checkpoint saving with W&B resume metadata.

Expected pattern:

- Training periodically saves a checkpoint such as `agent.pt` into the W&B run directory and calls `wandb.save(..., policy="now")`.
- On resume, the script detects `wandb.run.resumed`, reads a prior update or global step from the run summary, downloads the checkpoint, loads the model state, and continues from the next update.
- The user triggers resume with `WANDB_RUN_ID=<run-id>` and `WANDB_RESUME=must` or another intentional W&B resume policy.

Checks before resuming:

- Confirm the resumed script architecture and checkpoint class match the original run.
- Confirm the environment id, observation/action spaces, wrappers, and model hyperparameters are compatible.
- Confirm the checkpoint frequency was frequent enough that a recent checkpoint exists.
- Prefer a dry-run metadata check before launching full resumed training.
- Never print or store the W&B API key used to fetch the checkpoint.

## Reproduce Command Recovery

CleanRL's reproduce utility reads W&B run metadata and prints a recreation recipe that includes dependency installation and the original program/args. It is useful for reconstructing a run command, but it can contact W&B and should be treated as metadata access rather than local-only analysis.

Safe use:

- Validate W&B access first.
- Ask whether entity/team names should be removed from generated commands when sharing externally.
- Review recovered arguments for stale package versions, renamed scripts, removed flags, and sensitive values before execution.
- Treat the printed command as a starting point, not proof that the current checkout can reproduce the run exactly.

## Plotting Utilities

CleanRL's plotting utilities pull W&B run histories into pandas data frames, cache intermediate data by metric name, smooth curves, and export plots, legends, and data files. They can require W&B access, pandas, seaborn, matplotlib, NumPy, and sometimes a working LaTeX installation for text rendering.

Plotting checklist:

- Confirm the W&B project and metric key exist.
- Decide whether cached data should be reused or regenerated.
- Check `samples`, smoothing weight, y-axis label, output format, and interested experiment names before plotting.
- Expect plotting to create local cache, data, plot, and legend directories named after the metric key.
- If LaTeX rendering fails, disable TeX text rendering or use a simpler plot path rather than changing experiment data.
