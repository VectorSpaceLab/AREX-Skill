# Overview and Installation

## When to read

Read this for the package shape, install variants, entrypoint model, and the
safe checks to run before using deeper Diffusion Policy workflows.

## Repository shape

Diffusion Policy is a robotics imitation-learning codebase built around a
small set of reusable contracts:

- **Workspace**: owns the lifecycle of a training/evaluation run and checkpoint
  state. Workspaces inherit `BaseWorkspace` and are selected by Hydra workspace
  configs such as `train_diffusion_unet_lowdim_workspace` or
  `train_diffusion_unet_image_workspace`.
- **Task config**: selects a dataset adapter and an env runner. Task configs
  define `shape_meta`, horizon values, dataset paths, and runner parameters.
- **Dataset**: returns low-dimensional or image observation/action samples and
  provides a `LinearNormalizer` for matching policy inputs and outputs.
- **Policy**: implements `predict_action(obs_dict)` and `set_normalizer(...)`.
  Concrete families include diffusion UNet, diffusion Transformer, Robomimic,
  BET, and IBC variants.
- **EnvRunner**: evaluates a policy and returns loggable metrics and optional
  videos.
- **ReplayBuffer**: stores demonstration episodes in zarr directory or zip
  stores with `data/*` arrays and `meta/episode_ends`.

## Installation variants

The repository documents Conda-style environments rather than a dependency-rich
pip package:

| Variant | Use when | Important dependencies and limits |
|---|---|---|
| Simulation/Linux | Reproducing simulation benchmarks, Push-T, Robomimic, Kitchen, BlockPush | Python 3.9, PyTorch, CUDA toolkit, Hydra, zarr, gym, MuJoCo/robosuite/robomimic, diffusers, Ray, W&B |
| macOS development | Reading code and limited CPU development | No full benchmark support and no CUDA benchmark parity |
| Real robot | UR5 + RealSense + SpaceMouse workflows | Simulation stack plus `pyrealsense2`, `spnav`, `ur-rtde`, `atomics`, RealSense SDK, spacenavd, and hardware |

Do not install all variants just to inspect configs or data. Start with the
minimum environment for the requested task, then add simulator, CUDA, Ray, W&B,
or real-robot dependencies only when the workflow needs them.

## Package and import checks

The distribution name is `diffusion_policy`, but the repository does not expose
console entry points. The upstream training and evaluation interfaces are
project scripts plus config files, so actual benchmark runs normally happen in
a Diffusion Policy checkout or equivalent project layout.

Use the bundled root helper for safe checks:

```bash
python scripts/smoke_check.py --json
```

Optional checks:

```bash
python scripts/smoke_check.py --module diffusion_policy.common.replay_buffer
python scripts/smoke_check.py --config-root <config_root> --json
python scripts/smoke_check.py --cuda --json
```

If import works only from a checkout but not from a neutral current directory,
check packaging first: the repository uses a lightweight `setup.py` and many
users operate it directly from a checkout. For downstream automation, ensure
the project root or installed module path is available before launching the
upstream entrypoints.

## Entry point model

Use the sub-skills rather than treating this repository as a single CLI:

- Training/evaluation commands and Hydra overrides ->
  `sub-skills/training-and-evaluation/`.
- ReplayBuffer, dataset samples, conversions, and normalizers ->
  `sub-skills/data-and-replay-buffers/`.
- Policy/model interfaces, checkpoints, and action prediction ->
  `sub-skills/policies-and-models/`.
- UR5/RealSense/SpaceMouse, real demo/eval, and shared-memory IO ->
  `sub-skills/real-robot-operations/`.

## Data and artifact expectations

Training and evaluation runs may create:

- `.hydra/config.yaml`, `.hydra/hydra.yaml`, and `.hydra/overrides.yaml`.
- `logs.json.txt` for each run.
- `checkpoints/latest.ckpt` and top-k checkpoint files.
- `media/*.mp4` for rollout videos.
- For Ray multiruns: a shared `config.yaml`, `train_*/` directories, and a
  `metrics/` directory containing aggregate logs.

Real-robot workflows also create raw videos, camera metadata, low-dimensional
observations, and replay-buffer conversions. Treat those as hardware-gated data
operations; never run them as a generic smoke check.
