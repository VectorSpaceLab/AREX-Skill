# Plotting workflows

This reference covers RL Zoo result visualization from local files. It assumes the runtime package can import the plotting stack (`matplotlib`, `seaborn`, `scipy`, `pytablewriter`, and, for rliable plots, `rliable`). If non-plotting `rl_zoo3` commands work but plotting imports fail, resolve optional dependencies before using these recipes.

## Choose the command from the file format

| Available result file | Use | What it reads | What it produces |
| --- | --- | --- | --- |
| `*monitor.csv` files | `plot_train` | Training Monitor episode rows | A displayed training reward, success, or length curve. No built-in save flag. |
| `evaluations.npz` files | `all_plots` | Evaluation callback arrays from one or more runs | Learning curves, a Markdown results table on stdout, and optionally a postprocessed `.pkl`. |
| Postprocessed `.pkl` with `results_table` | `plot_from_file` | The `.pkl` exported by `all_plots` | Table on stdout, learning/final plots, optional image output, optional rliable plots. |
| Benchmark output table | Benchmark workflow | Reward logs generated while evaluating trained agents | `benchmark.md` under the benchmark directory. See [`benchmarking.md`](benchmarking.md). |

If only Monitor logs exist, do not force `all_plots`; use `plot_train` or route to [`../../training-cli/SKILL.md`](../../training-cli/SKILL.md) to create future runs with evaluation enabled. If `evaluations.npz` exists, prefer the two-step `all_plots` export plus `plot_from_file` render workflow because it can run headless and is reusable.

## Entry points

Equivalent installed-package plotting entry points are:

```bash
rl_zoo3 plot_train ...
rl_zoo3 all_plots ...
rl_zoo3 plot_from_file ...

python -m rl_zoo3.plots.plot_train ...
python -m rl_zoo3.plots.all_plots ...
python -m rl_zoo3.plots.plot_from_file ...
```

Use module entry points when the console router is unavailable. Use `MPLBACKEND=Agg` in CI, SSH, notebook kernels without a GUI, or any other headless runtime.

## Monitor CSV format for `plot_train`

`plot_train` calls the Stable-Baselines3 Monitor loader on each matching run folder. It expects Monitor CSV files in or under folders selected by:

```text
<exp-folder>/<algo>/<folder-name-containing-env>/.../*monitor.csv
```

The Monitor file normally starts with a JSON comment line and then a CSV header. Common columns are:

| Column | Meaning | Needed for |
| --- | --- | --- |
| `r` | Episode reward | `--y-axis reward` |
| `l` | Episode length | `--y-axis length` and timestep x-axis reconstruction |
| `t` | Wall-clock time | `--x-axis time` |
| `is_success` | Goal success flag, when the environment reports it | `--y-axis success` |

Important behavior:

- `--env` values are substring matches against run directory names, not strict Gymnasium ids.
- `--x-axis` choices are `steps`, `episodes`, or `time`.
- `--y-axis` choices are `reward`, `length`, or `success`.
- `--episode-window` controls rolling smoothing. If a timeseries has fewer episodes than the window, that run is skipped instead of plotted.
- `plot_train` always calls `plt.show()` and has no output-image flag. For noninteractive validation, use `MPLBACKEND=Agg`; for saved figures, prefer the `all_plots` + `plot_from_file` route when evaluation files are available.

Example:

```bash
MPLBACKEND=Agg rl_zoo3 plot_train \
  --algo ppo --env CartPole-v1 --exp-folder ./logs \
  --x-axis steps --y-axis reward --episode-window 20
```

## Evaluation NPZ format for `all_plots`

`all_plots` searches each experiment folder with this pattern:

```text
<exp-folder>/<algo-lowercase>/<folder-name-containing-env>/evaluations.npz
```

Each `evaluations.npz` must contain:

| Key | Expected shape | Meaning |
| --- | --- | --- |
| `timesteps` | `(n_eval,)` | Timestep at each evaluation point. |
| `results` | `(n_eval, n_eval_episodes)` | Episode rewards. This is the default `--key`. |
| other keys, e.g. `successes` | Usually `(n_eval, n_eval_episodes)` | Optional aggregate selected with `--key`. |

`all_plots` aggregates across matching run folders, removes incomplete runs that do not reach the selected evaluation length, and prints a Markdown table named `results_table`. When `--output <stem>` is provided, it writes `<stem>.pkl`; pass a stem, not a name ending in `.pkl`, to avoid accidental double suffixes.

Useful flags:

| Flag | Use |
| --- | --- |
| `--algos sac td3 tqc` | Algorithm names. Paths are looked up with lowercase names; table labels are uppercase. |
| `--env Half Ant` | Environment directory substring keys. These become environment keys in the exported pickle. |
| `--exp-folders ./logs ./other-logs` | One or more root folders containing algorithm subfolders. |
| `--labels baseline ablation` | One label per experiment folder. Required for readable multi-folder output. |
| `--key results` | Aggregate array key from `evaluations.npz`; use another key only if every file contains it. |
| `--min-timesteps` / `--max-timesteps` | Keep or truncate runs by evaluation horizon. |
| `--median` | Show median final evaluation instead of mean plus standard error. |
| `--no-display` | Do not show figures; use this for headless export. |
| `--print-n-trials` | Print the number of runs retained for each env/algo/folder. |

Headless export example:

```bash
rl_zoo3 all_plots \
  --algos sac td3 tqc \
  --env Half Ant \
  --exp-folders ./logs \
  --labels local \
  --output ./plots/offpolicy \
  --no-display --print-n-trials
```

This writes `./plots/offpolicy.pkl` when input evaluation files are complete enough.

## Postprocessed pickle format for `plot_from_file`

`plot_from_file` expects a pickle created by `all_plots`. The top-level object is a dictionary with:

```text
{
  "results_table": {
    "headers": ["Environments", ...],
    "value_matrix": [[...], ...]
  },
  "<env-key>": {
    "<ALGO-label>": {
      "timesteps": array shape (n_eval,),
      "mean": array shape (n_eval,),
      "std_error": array shape (n_eval,),
      "last_evals": array shape (n_trials,),
      "std_error_last_eval": scalar,
      "mean_per_eval": array shape (n_eval, n_trials)  # needed for --iqm sample-efficiency plots
    }
  }
}
```

`plot_from_file` prints the stored results table, optionally merges additional result files with `--merge`, filters with `--skip-envs`, `--keep-envs`, `--skip-keys`, or `--keep-keys`, and can save the final sensitivity plot with `--output` and `--format`.

Headless render example:

```bash
MPLBACKEND=Agg rl_zoo3 plot_from_file \
  --input ./plots/offpolicy.pkl \
  --skip-timesteps \
  --output ./plots/offpolicy.svg \
  --format svg
```

`plot_from_file` appends `.pkl` to `--input` only when the input string does not already end in `.pkl`.

## Rliable plots and normalization caveats

Enable rliable with `--rliable`; add `--versus` for probability-of-improvement plots and `--iqm` for the IQM sample-efficiency curve. Example:

```bash
MPLBACKEND=Agg rl_zoo3 plot_from_file \
  --input ./plots/offpolicy.pkl \
  --skip-timesteps \
  --rliable --versus --iqm \
  --labels SAC TD3 TQC \
  --output ./plots/offpolicy_rliable.svg \
  --format svg
```

Interpretation rules:

- Rliable requires the optional `rliable` package and its dependency stack. It can be slow because bootstrap confidence intervals are computed.
- `--labels` must have the same count as the plotted method keys. Mismatches fail early because labels are zipped strictly.
- Normalized-score plots are only trustworthy when every environment key is mapped to the intended environment id and the min/max reference score is defined. Built-in mappings cover the keys `Half`, `Ant`, `Hopper`, `Walker`, `LunarLanderContinuous`, and `BipedalWalker` for the corresponding PyBullet/Box2D ids. Other keys trigger warnings or produce raw-score comparisons under a normalized-score label.
- The reference-score table is small and hand-curated; do not present rliable output as a quantitative benchmark when environment normalization is missing, stale, or mixed across environment versions.

## Non-executing command builder

Use the bundled helper to assemble commands and optionally validate local input presence before any plotting call:

```bash
python scripts/plotting_command_builder.py --help
python scripts/plotting_command_builder.py --check-inputs all-plots \
  --algos sac td3 --envs Half Ant --exp-folders ./logs --labels local --output ./plots/offpolicy
```

The helper never imports `rl_zoo3`, never opens a display, never contacts external services, and never launches the command it prints.
