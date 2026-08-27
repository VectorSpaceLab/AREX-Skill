# Logs, Plots, and GIFs

This reference gathers the repository's logging and visualization conventions.

## Log schema

Training writes CSV rows with these columns:

- `episode`
- `timestep`
- `reward`

The native plotting script reads one or more CSV files from `PPO_logs/<env_name>/` and averages multiple runs by index when requested.

## Plotting behavior

The original `plot_graph.py` script:

- creates `PPO_figs/<env_name>/` if needed,
- reads every CSV in the environment log directory,
- smooths the reward curve,
- and writes `PPO_<env_name>_fig_<fig_num>.png`.

The bundled helper keeps the same layout but is safer to run from arbitrary directories.

### Default helper usage

```bash
python scripts/plot_training_logs.py --env-name CartPole-v1 --log-root PPO_logs --output-root PPO_figs
```

If you already know the exact CSV files, pass them explicitly instead of relying on the default layout.

## Smoothing notes

The native plotting code uses a triangular rolling window to draw a smoother line and a lower-opacity variance line. The bundled helper uses a dependency-light moving-average fallback so it does not need any extra plotting packages beyond pandas and matplotlib.

## GIF composition behavior

The native GIF workflow has two distinct parts:

1. Save frames for each timestep in `PPO_gif_images/<env_name>/`.
2. Compose the GIF in `PPO_gifs/<env_name>/`.

The bundled helper only handles the second part: composition from already-saved image frames.

### Default helper usage

```bash
python scripts/make_training_gif.py --images-glob 'PPO_gif_images/CartPole-v1/*.jpg' --output PPO_gifs/CartPole-v1/PPO_CartPole-v1_gif_0.gif
```

## Where the notebook fits

The notebook demonstrates a headless or remote render path with virtual-display packages. That path is useful as evidence for dependency choices, but it is not the default runtime path in this skill because it depends on the live environment backend.

## When to read this file

Read this file when you need the output layout, the log column schema, the smoothing behavior, or the frame-to-GIF separation.
