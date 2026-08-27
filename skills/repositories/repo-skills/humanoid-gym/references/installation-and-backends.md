# Installation and backends

## Purpose

Read this before building commands or attempting native execution. Humanoid-Gym is a Python 3.8-era robotics repo with a manual Isaac Gym dependency for the main training/evaluation path and MuJoCo for sim-to-sim deployment.

## Verified runtime stack

Source and inspection evidence point to this runtime combination:

- Python 3.8
- `humanoid==1.0.0`
- PyTorch `1.13.1+cu117` or a matching CUDA 11.7-era build
- NumPy `1.23.5`
- SciPy `1.10.1`
- `mujoco==2.3.6`
- `mujoco-python-viewer`
- `opencv-python`
- `wandb`
- `tensorboard`
- `tqdm`
- `DateTime`

## Backend expectations

### Isaac Gym training/evaluation

The main `train.py` and `play.py` workflows require Isaac Gym Preview 4. That backend is not installable from public PyPI and must usually be installed manually from NVIDIA's distribution.

Use this route only when all of the following are true:

- Isaac Gym Preview 4 is installed and importable.
- PyTorch and the NVIDIA driver/runtime are compatible.
- `--sim_device` and `--rl_device` are aligned the way the README recommends.
- You are prepared for W&B/TensorBoard logging side effects during training.

### MuJoCo sim-to-sim

The sim-to-sim path needs MuJoCo plus a viewer/display stack.
A CPU-only or headless environment can still validate asset existence and policy shape with the bundled validator, but it cannot prove the rendered rollout.

## Install shape

For a local editable checkout, the common pattern is:

1. Create a private Python 3.8 environment.
2. Install the runtime packages for the selected route.
3. Install this repository in editable mode.
4. Confirm `import humanoid`.
5. Run `python -m pip check`.
6. For training/play, confirm Isaac Gym Preview 4 is importable.

## Minimal public smoke check

```bash
python -c "import humanoid; print(humanoid.LEGGED_GYM_ROOT_DIR)"
```

This only checks the package root and does not prove Isaac Gym runtime readiness.

## Route-specific notes

- Training/evaluation route: use the `training-and-evaluation` sub-skill.
- Environment customization route: use the `environment-customization` sub-skill.
- Sim-to-sim route: use the `sim2sim-deployment` sub-skill.
