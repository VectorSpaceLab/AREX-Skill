# RL Library Matrix

## Unified entrypoints

Isaac Lab exposes one `train` wrapper and one `play` wrapper that dispatch to a selected reinforcement learning library through `--rl_library`.

Supported library names seen in the source and docs:

- `rl_games`
- `rsl_rl`
- `sb3`
- `skrl`
- `rlinf` for the contributed path in `isaaclab_contrib`

## Library-specific install extras

- `rl_games` — install the `rl_games` extra from the `isaaclab_rl` package.
- `rsl_rl` — install the `rsl_rl` extra from the `isaaclab_rl` package.
- `sb3` — install the `sb3` extra from the `isaaclab_rl` package.
- `skrl` — install the `skrl` extra from the `isaaclab_rl` package.
- `rlinf` — install the `rlinf` extra from the `isaaclab_contrib` package.

The RL packages share core dependencies such as `numpy`, `torch`, `torchvision`, `protobuf`, `hydra-core`, `h5py`, `tensorboard`, `moviepy`, `pillow`, `packaging`, and `tqdm`. The source setup files also pin library-specific extras where needed.

## Common train/play arguments

Shared flags seen across the wrappers include:

- `--task`
- `--agent`
- `--seed`
- `--num_envs`
- `--distributed`
- `--max_iterations`
- `--video`
- `--video_length`
- `--video_interval`
- `--checkpoint`
- `--load_run`
- `--export_io_descriptors`
- `--ray-proc-id`

The `play` path also accepts the library-specific checkpoint location conventions used by the selected implementation.

## Typed preset compatibility

The RL wrappers preserve the typed preset tokens on the remainder passed through Hydra. Supported command forms include:

```bash
./isaaclab.sh train --rl_library rsl_rl --task Isaac-Ant-v0 physics=newton_mjwarp
./isaaclab.sh play --rl_library rsl_rl --task Isaac-Reach-Franka-v0 presets=rgb
```

The important constraint is that the same observation-affecting preset must be used for both training and playback when the checkpoint input shape depends on that preset.

## Checkpoint conventions

- `rl_games` uses run directories with model checkpoint files under `nn/`.
- `rsl_rl` commonly stores checkpoints under a run directory selected by `--load_run`.
- `sb3` and `skrl` use their library-specific model filename conventions.

When a task supports video capture, evaluation commands often need `--video` and `--video_length` to produce replay artifacts.

## Distributed and cloud paths

The contributed `rlinf` path and the `scripts/reinforcement_learning/ray/` helpers are related to distributed or cloud-style workflows. Treat those as higher-risk deployment tooling rather than the default local train/play path.
