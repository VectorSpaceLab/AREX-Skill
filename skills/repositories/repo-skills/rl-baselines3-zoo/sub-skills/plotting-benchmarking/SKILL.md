---
name: plotting-benchmarking
description: "Plot RL Baselines3 Zoo training/evaluation results and build safe
  benchmark result commands."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# plotting-benchmarking

Use this sub-skill when a future Researcher needs RL Baselines3 Zoo plotting or benchmark-result workflows from an installed `rl_zoo3` package: training monitor curves, evaluation curves, postprocessed result pickles, rliable comparison plots, or bounded benchmark-table commands.

## Route here for

- Plotting training reward, episode length, or success curves from Monitor CSV files with `rl_zoo3 plot_train` or `python -m rl_zoo3.plots.plot_train`.
- Aggregating evaluation callback files named `evaluations.npz` with `rl_zoo3 all_plots` or `python -m rl_zoo3.plots.all_plots`.
- Rendering postprocessed `.pkl` result files with `rl_zoo3 plot_from_file` or `python -m rl_zoo3.plots.plot_from_file`, including `--rliable`, `--versus`, and `--iqm` options.
- Building a safe benchmark command using `python -m rl_zoo3.benchmark --test-mode --no-hub`.
- Diagnosing missing plotting dependencies, headless display failures, missing evaluation files, rolling-window issues, normalization caveats, or benchmark Hub surprises.

## Route elsewhere

- Model/artifact folder selection, `best_model.zip`, checkpoint/latest model loading, and no-render `enjoy` evaluation: [`../evaluation-and-artifacts/SKILL.md`](../evaluation-and-artifacts/SKILL.md).
- Optuna HPO study/report generation before plotting its outputs: [`../tuning-optimization/SKILL.md`](../tuning-optimization/SKILL.md).
- Live Hugging Face Hub downloads/uploads or service credentials during benchmarking: [`../integrations-hub-tracking/SKILL.md`](../integrations-hub-tracking/SKILL.md).
- Producing training logs or adding evaluation callbacks to a run: [`../training-cli/SKILL.md`](../training-cli/SKILL.md).
- Optional dependency and console-entry import caveats shared across the repo skill: [`../../references/install-and-environment.md`](../../references/install-and-environment.md).

## Default operating stance

1. Identify the available result format first: Monitor CSV files imply `plot_train`; `evaluations.npz` files imply `all_plots`; an exported result `.pkl` implies `plot_from_file`; benchmark tables imply `python -m rl_zoo3.benchmark`.
2. Prefer installed-package entry points. Use `python -m rl_zoo3.plots.<module>` if the `rl_zoo3` console router is unavailable; use `rl_zoo3 <plot_subcommand>` when plotting extras import successfully.
3. For headless sessions, add `MPLBACKEND=Agg`; also pass `--no-display` to `all_plots`. `plot_train` and `plot_from_file` call `plt.show()`, so the backend guard is the no-display safety mechanism.
4. Treat rliable output as optional and comparatively slow because it bootstraps confidence intervals. Check normalization coverage before interpreting “normalized score” plots.
5. Keep benchmark commands offline and bounded by default: include both `--test-mode` and `--no-hub`, and use a caller-controlled benchmark directory.

## Bundled references and helper

- [`references/plotting-workflows.md`](references/plotting-workflows.md) explains data formats, command recipes, and rliable interpretation boundaries.
- [`references/benchmarking.md`](references/benchmarking.md) explains benchmark inputs, outputs, and side-effect controls.
- [`references/troubleshooting.md`](references/troubleshooting.md) maps common plotting/benchmark failures to fixes.
- [`scripts/plotting_command_builder.py`](scripts/plotting_command_builder.py) builds non-executing plotting/benchmarking commands and can statically validate input files.

## Minimal safe command-building examples

```bash
python scripts/plotting_command_builder.py \
  all-plots --algos sac td3 tqc --envs Half Ant --exp-folders ./logs \
  --labels local --output ./plots/offpolicy --print-n-trials

python scripts/plotting_command_builder.py \
  plot-from-file --input ./plots/offpolicy.pkl --skip-timesteps --rliable --versus \
  --labels SAC TD3 TQC --output ./plots/offpolicy.svg

python scripts/plotting_command_builder.py \
  benchmark --log-dir ./rl-trained-agents --benchmark-dir ./benchmark-output \
  --n-timesteps 100 --num-threads 1
```

The helper prints commands only; it does not train, evaluate, open figures, contact the Hub, or write benchmark/plot output files.
