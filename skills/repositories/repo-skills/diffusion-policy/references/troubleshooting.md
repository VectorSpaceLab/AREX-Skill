# Cross-cutting Troubleshooting

## Import and packaging

| Symptom | Likely cause | What to do |
|---|---|---|
| `ModuleNotFoundError: diffusion_policy` outside the project root | The repo's lightweight packaging does not expose console scripts and may be operated directly from a checkout | Run `scripts/smoke_check.py --json`; ensure the project root or installed module path is on Python's module path before launching upstream scripts |
| `PackageNotFoundError: diffusion_policy` | Editable install or distribution metadata is missing | Install the repo package for the active environment or operate from a correctly configured checkout |
| Importing model modules fails on `torch`, `diffusers`, `huggingface_hub`, or `numba` | Minimal environment lacks model/diffusion dependencies or has incompatible versions | Install the documented simulation environment or add only the missing dependency group needed for the workflow; see the owning sub-skill troubleshooting file |
| `pip check` reports incompatible packages | Mixing old pinned robotics dependencies with newer packages | Prefer a fresh Python 3.9 Conda environment; avoid upgrading only one package in a pinned stack unless the whole compatibility set is reviewed |

## Hydra and configuration

| Symptom | Likely cause | What to do |
|---|---|---|
| `Cannot find primary config` | Wrong config root or config name | Use `sub-skills/training-and-evaluation/scripts/compose_experiment_config.py --config-root <config_root> --config-name <name> --print-targets` before starting a run |
| Task dataset path is missing | The task config expects a downloaded training dataset or a real demo replay buffer | Route to `data-and-replay-buffers` to inspect expected store layout and normalizer keys |
| `shape_meta` and policy shapes disagree | Workspace config and task config are mismatched, or an override changed horizons/actions | Compare `shape_meta`, `horizon`, `n_obs_steps`, and `n_action_steps`; route to `policies-and-models` for policy shape rules |
| Run outputs appear in an unexpected directory | Hydra's `hydra.run.dir` or `multi_run.run_dir` was overridden | Inspect `.hydra/overrides.yaml` in the run output or compose the intended config before rerunning |

## Data and checkpoints

| Symptom | Likely cause | What to do |
|---|---|---|
| ReplayBuffer has wrong episode count | `meta/episode_ends` is missing, not increasing, or mismatched with `data/*` lengths | Run `data-and-replay-buffers/scripts/inspect_replay_buffer.py --path <store>` and fix the conversion/export step |
| Evaluation checkpoint will not load | Checkpoint is incomplete, not a Diffusion Policy workspace checkpoint, or code/config family changed | Confirm the checkpoint payload contains `cfg`, `state_dicts`, and the expected model/EMA keys; choose a checkpoint produced by the same workspace family |
| Evaluation score differs from training score | Wrong task runner, non-EMA weights, wrong seed range, missing normalizer, or device/backend difference | Inspect the checkpoint config, `training.use_ema`, task env runner target, and output log keys |

## CUDA, simulators, and optional hardware

| Symptom | Likely cause | What to do |
|---|---|---|
| `torch.cuda.is_available()` is false | CPU-only PyTorch build, missing driver/runtime, or hidden GPUs | Use `scripts/smoke_check.py --cuda --json`; install a PyTorch build compatible with the driver and GPU |
| CUDA import works but kernels fail | Wheel does not support the GPU compute capability or a compiled extension ABI mismatches Torch | Match PyTorch/CUDA versions to the hardware; do not count import success as full benchmark readiness |
| MuJoCo/robosuite/robomimic import fails | Simulator dependencies and system OpenGL packages are missing | Use the documented simulation environment and install required system libraries; do not debug this in a real-robot environment first |
| W&B login or network calls block a run | Online logging is enabled in a non-interactive environment | Use offline/disabled logging mode when appropriate and keep data downloads outside smoke checks |
| RealSense, SpaceMouse, or RTDE imports fail | Real-robot dependency stack or system services are missing | Route to `real-robot-operations` and run its safe prereq checker; do not start demo/eval until hardware and safety preflight pass |

## Stop conditions

Stop and ask for explicit operator confirmation before any workflow that:

- Commands a UR robot or moves hardware.
- Starts camera recording for real data collection.
- Downloads large datasets or checkpoints.
- Launches Ray workers or multi-GPU training.
- Overwrites a checkpoint/evaluation output directory.
- Requires credentials, private data, or network-only resources.
