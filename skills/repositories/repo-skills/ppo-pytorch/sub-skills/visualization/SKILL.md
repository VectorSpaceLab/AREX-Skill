---
name: visualization
description: "Plot PPO reward logs and compose GIFs from saved frame images."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Visualization

Use this sub-skill when the user wants to plot training rewards, compare multiple runs, compose a GIF from saved frames, inspect the CSV log schema, or understand why a plotting or GIF step failed.

Do not use this sub-skill for training-loop changes or pretrained checkpoint evaluation. Route those tasks to the sibling sub-skills. Route low-level PPO class behavior to the root [API reference](../../references/api-reference.md).

## What this sub-skill owns

- The `PPO_logs/<env_name>/PPO_<env_name>_log_<run_num>.csv` schema.
- Reward smoothing and average-over-runs plotting.
- Figure output naming and directory layout.
- GIF composition from already-saved image frames.
- Headless plotting and image-ordering failure modes.

## Quick workflow

1. **Check the log or frame layout first.** Use the bundled helpers from this sub-skill directory:

   ```bash
   python scripts/plot_training_logs.py --help
   python scripts/make_training_gif.py --help
   ```

2. **Plot logs from one environment.** If your logs live in the default layout, point the helper at the environment name and log root. The helper will discover the run CSVs and write a PNG into the figure directory.

3. **Compose a GIF from frames.** The GIF helper expects an ordered set of JPEG or PNG frames, usually already saved by a separate render step.

4. **Keep frame capture separate from composition.** Environment rendering depends on Gym, Roboschool, or another environment backend. GIF composition only needs Pillow and image files.

## Core references

- [Logs, plots, and GIFs](references/logs-plots-and-gifs.md) - CSV schema, smoothing choices, output layout, and helper usage.
- [Troubleshooting](references/troubleshooting.md) - missing columns, missing frames, headless plotting, and image or Pillow problems.
- [Root PPO API reference](../../references/api-reference.md) - shared PPO behavior only when you need to trace outputs back to the model.

## Validation commands

Safe checks for this sub-skill should stay small and deterministic:

```bash
python scripts/plot_training_logs.py --help
python scripts/make_training_gif.py --help
python -m py_compile scripts/plot_training_logs.py scripts/make_training_gif.py
```

A tiny CSV or tiny image fixture is enough to verify the helpers. Do not default to a live environment render unless the user explicitly needs that dependency-bound path.
