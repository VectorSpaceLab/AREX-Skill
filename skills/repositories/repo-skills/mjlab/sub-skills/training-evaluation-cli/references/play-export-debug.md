# Play, export, and debug

This page covers the installed playback, export, and NaN-debug CLIs. It also
summarizes when the command is safe, interactive, or networked.

## Command safety

| Command | Safety | Typical use |
|---|---|---|
| `uv run play <TASK> --help` | safe | inspect playback flags |
| `uv run play <TASK> --agent zero` | bounded | sanity-check a config without a policy |
| `uv run play <TASK> --agent random` | bounded | spot obvious MDP issues |
| `uv run play <TASK> --checkpoint-file ...` | long-ish | evaluate a local checkpoint |
| `uv run play <TASK> --wandb-run-path ...` | networked | evaluate from W&B |
| `uv run export-scene <TARGET>` | local | write XML/assets for inspection |
| `uv run viz-nan <DUMP>` | local | inspect a NaN dump |
| `uv run demo` | networked | download demo assets and launch playback |

## `play` command behavior

`play` is the installed evaluation and debugging command. It accepts dummy
policies, local checkpoints, W&B checkpoints, and motion files.

Key flags:

- `--agent zero|random|trained`
- `--checkpoint-file` for a local checkpoint
- `--wandb-run-path` and `--wandb-checkpoint-name` for W&B-backed playback
- `--motion-file` for local motion imitation playback
- `--registry-name` when a tracking task needs a motions registry artifact
- `--device` to force CPU or a specific CUDA device
- `--num-envs` to override the play-time environment count
- `--viewer auto|native|viser`
- `--video`, `--video-length`, `--video-height`, and `--video-width`
- `--camera` to select a camera by index or name
- `--no-terminations` to keep a motion running for inspection

### Input resolution rules

For tracking tasks:

1. A local `--motion-file` wins if it exists.
2. Dummy-agent play requires either a local motion file or `--registry-name`.
3. Trained play can use `--motion-file`, or it can resolve the motion artifact
   from the W&B run.
4. If the run has no motion artifact, playback should fail early rather than
   silently using the wrong data.

For trained play:

1. A local `--checkpoint-file` wins if provided and exists.
2. Otherwise `--wandb-run-path` is required.
3. `--wandb-checkpoint-name` narrows the model within that run.

### Viewer choice

- `auto` selects native when a display is available and Viser otherwise
- `native` is best for local iteration and interactive perturbations
- `viser` is best for browser-based or remote debugging

### Video capture

`--video` records play rollouts with the offscreen renderer. Keep it bounded:

- use `--video-length` to cap the clip length
- set `--video-height` and `--video-width` if the default resolution is too large
- expect rendering to depend on the host's GL/EGL setup

### Hot-swapping checkpoints

When a trained policy is opened in the Viser viewer, the UI can list local or
W&B checkpoints for hot-swapping. This is useful for comparing checkpoints
without relaunching the whole playback process.

## `export-scene`

`export-scene` writes a self-contained scene directory or zip archive.

Target resolution order:

1. task ID from the live registry
2. built-in alias such as `g1`, `go1`, or `yam`
3. import-path callable that returns an entity config

Output behavior:

- the output directory is cleaned before export
- the export contains `scene.xml` and an `assets/` directory
- `--zip True` creates a zip archive instead of leaving the directory behind
- unknown targets print the available task IDs and aliases

## `viz-nan`

`viz-nan` inspects a NaN dump directory produced by the NaN guard.

- the input is a `nan_dump_*.npz` file
- the companion `model_*.mjb` must sit alongside it
- the viewer provides step and environment sliders
- it is intended for local postmortem debugging, not for long automation

## `demo`

`demo` is a convenience launcher for a pretrained tracking showcase.
It downloads a checkpoint and a motion file, caches them locally, and then runs
`play` with a browser viewer.

Important caveats:

- it is networked before it is interactive
- it is not a safe offline help-only command
- it is meant as a showcase, not as a generic task launcher

## Practical debugging order

1. confirm the task exists with `list-envs`
2. inspect `train --help` and `play --help`
3. validate the checkpoint or motion input with the bundled helpers
4. use `play --agent zero` or `play --agent random` for bounded sanity checks
5. only then move to long GPU training or W&B-backed playback
