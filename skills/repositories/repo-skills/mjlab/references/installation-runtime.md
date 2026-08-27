# Installation and runtime

Use this reference to choose an installation path and set expectations before
running mjlab workflows.

## Installation paths

### New uv project

```bash
uv init --package my_mjlab_project
cd my_mjlab_project
uv add mjlab
uv run demo --help
```

Use this when mjlab is a dependency of another robotics/RL project.

### Source checkout for development

```bash
uv sync
uv run list-envs
uv run train Mjlab-Cartpole-Balance --help
```

Use `uv run` for commands from the checkout. Do not rely on a globally active
Python environment.

### Classic pip/venv/conda

```bash
pip install mjlab
list-envs
```

This is acceptable for users who do not use uv, but uv is the project's most
well-documented path and exposes extras/index choices consistently.

### Docker or clusters

For NVIDIA training in containers, use an image/runtime that exposes GPUs to
CUDA and MuJoCo's EGL rendering stack. A minimal local pattern is:

```bash
docker run --rm --runtime=nvidia --gpus all ghcr.io/mujocolab/mjlab uv run demo
```

Cloud/SkyPilot templates and W&B sweeps are credentialed, cost-incurring
workflows. Treat them as opt-in operational tasks, not safe smoke checks.

## Backend expectations

| Workflow | CPU-only | CUDA-capable NVIDIA host |
|---|---|---|
| import `mjlab`, inspect configs, list tasks, CLI help | supported | supported |
| run some lightweight CPU evaluation/config checks | possible | possible |
| training with many parallel environments | not sufficient | expected path |
| camera/raycast/rendering with MuJoCo Warp at scale | partial at best | expected path, with EGL/GL configured |
| distributed training with `--gpu-ids` list/all | no | requires multiple visible GPUs |

mjlab sets `MUJOCO_GL=egl` by default on Linux at import time when the variable
is not already set. Override it only when the host requires a different MuJoCo
GL backend.

## Environment smoke check

Use the bundled smoke script to confirm the installed package, task registry,
CLI entry points, and optional CUDA visibility:

```bash
uv run python path/to/mjlab_environment_smoke.py --json
```

Expected signals:

- `mjlab` distribution version prints.
- `list-envs`-equivalent registry import finds built-in task IDs.
- `torch` imports.
- If CUDA is visible, `torch.cuda.is_available()` is true and a tiny tensor can
  be allocated.

## Common command syntax

Tyro is strict in mjlab CLIs:

```bash
uv run train Mjlab-Velocity-Flat-Unitree-G1 \
  --env.scene.num-envs 4096 \
  --agent.resume True \
  --gpu-ids "[0, 1]"
```

- Use hyphenated CLI names even when Python fields use underscores.
- Pass explicit `True` / `False` for booleans.
- Quote Python-list literals in shells.
- Use `--help` for the exact task-specific nested flag surface.

## Credentials and network

These workflows may require network, W&B login, cloud credentials, or large
artifacts:

- `uv run demo`
- `play` or `train` with W&B run paths or registry names
- tracking motion registry downloads
- cloud launch and sweep jobs
- benchmark report generation

Validate local config/CLI shape first, then ask for explicit authorization
before running a networked or cost-incurring command.
