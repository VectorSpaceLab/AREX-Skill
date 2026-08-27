# Data and Artifact Conventions

## When to read

Read this for checkpoint, log, monitor CSV, historical result, and GAIL expert-data artifacts.

## Checkpoints

Training saves checkpoints as a two-item PyTorch object:

```text
[actor_critic, obs_rms]
```

The path is built as:

```text
<save-dir>/<algo>/<env-name>.pt
```

`actor_critic` is the `Policy` instance. `obs_rms` is the observation-normalization state from `VecNormalize` when present, otherwise `None`. Playback needs the same normalization state for vector observations.

## Logs and monitor CSVs

`--log-dir` is passed into Stable-Baselines3's `Monitor` wrapper for each environment rank. The utility `cleanup_log_dir` creates the directory or removes existing `*.monitor.csv` files before a new run. Evaluation uses a sibling path formed by appending `_eval` to the training log directory.

Historical `logs/` and `time_limit_logs/` directories are experiment outputs, not required runtime inputs for this skill. Use them only as evidence of monitor CSV layout or result plotting conventions.

## GAIL expert artifacts

GAIL expects a PyTorch `.pt` file with keys:

- `states`
- `actions`
- `rewards`
- `lengths`

The training loop builds the expected filename from the environment prefix:

```text
<training gail experts dir>/trajs_<lowercase env prefix>.pt
```

For example, `HalfCheetah-v2` maps to `trajs_halfcheetah.pt`. See `sub-skills/gail-imitation/` for the HDF5 conversion schema and bundled converter.

## Visualization

The repository contains historical image outputs and a plotting notebook, but this generated skill does not bundle notebook execution. If a user asks to plot results, first identify the monitor CSV columns from the user's run output, then build a fresh plotting script for those CSVs rather than relying on the original notebook.
