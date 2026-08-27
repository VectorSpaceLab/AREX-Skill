# Troubleshooting Optuna HPO

Use this page when an RL Zoo task is already confirmed to be an HPO or study-artifact problem. For ordinary training errors, route to [`../../training-cli/SKILL.md`](../../training-cli/SKILL.md); for config syntax, route to [`../../config-hyperparams/SKILL.md`](../../config-hyperparams/SKILL.md).

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `--pruner halving` fails or is rejected in planning | Successive halving needs parallel jobs in RL Zoo's tuning workflow. | Use `--n-jobs 2` or higher, or switch to `--pruner median` / `--pruner none` for single-job runs. |
| `--sampler auto` fails before trials start | The auto sampler imports `optunahub`, which is optional. | Install/enable `optunahub` in the runtime environment or use `--sampler tpe` / `--sampler random`. |
| `--trial-id` does not load tuned parameters | The train CLI only loads a study trial when `--storage`, `--study-name`, and `--trial-id` are all present. | Supply the exact storage backend and study name used during HPO. Remember that `--trial-id` is the stored trial number/index, not the rank in a sorted report. |
| Storage is supplied but later workers cannot join the same study | The original run omitted `--study-name`, so Optuna generated a name that may not be known to other commands. | Always set a stable `--study-name` when using `--storage` for distributed optimization or replay. |
| Distributed HPO exceeds or undershoots the expected trial count | `--n-trials` is per runner. `--max-total-trials` is the cross-study cap and counts `COMPLETE`, `RUNNING`, and `PRUNED` trials. | For distributed work, run every worker with the same `--storage`, same `--study-name`, and the same `--max-total-trials`. Expect one worker may do fewer trials when the cap is nearly reached. |
| A trial is pruned after a NaN, assertion, or value error | RL Zoo treats invalid sampled hyperparameters as prunable candidates. | This is expected HPO behavior. Reduce risky search-space changes, use a more conservative sampler/pruner, or inspect per-trial logs if `--optimization-log-path` was enabled. |
| No final plots appear, or plots fail in a headless environment | `--no-optim-plots` suppresses optional Optuna plots; missing plot dependencies or no display can also prevent plotting. | Keep `--no-optim-plots` for unattended runs. CSV/pickle reports are still written. Route later visualization to [`../../plotting-benchmarking/SKILL.md`](../../plotting-benchmarking/SKILL.md). |
| `rl_zoo3 train` fails on import before reaching training flags | The console entry imports plot modules before dispatching to train, so optional plot dependencies can matter even for train commands. | Prefer `python -m rl_zoo3.train` for HPO command templates, or ensure the plotting optional dependencies are installed. See [`../../../references/install-and-environment.md`](../../../references/install-and-environment.md). |
| HPO is too slow or expensive | Each trial is a full bounded train/eval run, and default trial counts can be large. | First reduce `-n/--n-timesteps`, `--n-trials` or `--max-total-trials`, `--n-evaluations`, and optional expensive environments. Use `--trial-id` to replay an existing good trial instead of searching again. |
| Per-trial evaluation files are missing | `--optimization-log-path` was not set, or the trial ended before an evaluation artifact was written. | Add `--optimization-log-path <dir>` for future runs and make sure `--n-evaluations` and `-n/--n-timesteps` allow at least one evaluation. |

## Command-builder guardrails

The bundled `scripts/tuning_command_builder.py` is intentionally non-executing. It refuses or warns about the highest-risk combinations before printing a command string:

- errors on unsupported HPO algorithms, `--pruner halving` with `--n-jobs <= 1`, `--sampler auto` when `optunahub` is unavailable, negative/zero counts, and `--trial-id` without both storage and study name;
- warns when no explicit `-n/--n-timesteps` budget is visible in passthrough training args;
- warns that `--max-total-trials` takes precedence over `--n-trials` and should be paired with shared storage/study name for distributed workers;
- defaults generated optimization commands to `--no-optim-plots` unless explicitly asked to show plots.
