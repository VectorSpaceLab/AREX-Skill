# Install and Extras Reference

## Purpose

Read this when installing CleanRL, choosing optional dependencies, or diagnosing import/help failures. CleanRL is a Python package with script entrypoints and optional backend families; install only the dependency set needed for the selected workflow.

## Package Facts

- Distribution name: `cleanrl`.
- Verified package version for this skill snapshot: `2.0.0b1`.
- Supported Python range in package metadata: `>=3.8,<3.11`.
- Core dependencies include torch, Gym, Gymnasium, TensorBoard, W&B, MoviePy, Pygame, Hugging Face Hub, Rich, Tenacity, and Tyro.
- CleanRL is not primarily a modular library. Treat `cleanrl/` files as runnable training scripts and `cleanrl_utils/` as utilities.

## Base Install

```bash
pip install cleanrl
python - <<'PY'
import importlib.metadata as metadata
print(metadata.version('cleanrl'))
import cleanrl_utils
print('cleanrl_utils ok')
PY
```

For local development in a checkout, editable install is useful:

```bash
pip install -e .
```

Use Python 3.10 when possible for this repository generation. Avoid Python 3.11+ unless the upstream package metadata and backend wheels have changed.

## Optional Extras by Workflow

| Extra or requirement family | Use when | Typical owners |
| --- | --- | --- |
| `atari` | Atari scripts such as `dqn_atari.py`, `ppo_atari.py`, C51/Rainbow/SAC Atari, ROM wrappers | `training-scripts`, `evaluation-and-sharing` |
| `envpool` | EnvPool Atari scripts and RND/PQN EnvPool variants | `training-scripts` |
| `procgen` | `ppo_procgen.py` and `ppg_procgen.py` | `training-scripts` |
| `mujoco` | MuJoCo continuous-control scripts such as SAC/TD3/DDPG/PPO continuous action | `training-scripts` |
| `dm_control` | DM Control env ids such as `dm_control/cartpole-balance-v0` | `training-scripts` |
| `pettingzoo` | Multi-agent Atari PettingZoo PPO | `training-scripts` |
| `jax` | JAX variants such as `dqn_jax.py`, `c51_jax.py`, EnvPool XLA scripts | `training-scripts` |
| `optuna` | Hyperparameter tuning with `cleanrl_utils.tuner` | `experiment-operations` |
| `cloud` | AWS Batch/cloud submission utilities | `experiment-operations` |
| `docs` | Building MkDocs documentation | `repo-maintenance` |

Do not install every extra as a first response. Optional backends are large, platform-sensitive, or credential/hardware dependent.

## Backend Notes

- **Torch/CUDA**: Core torch import can work on CPU; GPU execution requires a torch wheel compatible with the host driver and GPU architecture.
- **Atari**: ROM/license setup and OpenCV/shimmy dependencies can fail independently of CleanRL.
- **JAX**: CPU/GPU/TPU wheels differ. Do not assume JAX is installed just because torch works.
- **MuJoCo/DM Control**: Requires native wheels/system support and compatible environment ids.
- **EnvPool**: Linux-specific in CleanRL docs and not interchangeable with Gym/Gymnasium envs.
- **IsaacGym**: Requires NVIDIA IsaacGym assets and older documented Python/CUDA constraints; treat as special setup, not a normal pip extra.

## Safe Verification

```bash
python scripts/check_cleanrl_environment.py --check-help
python sub-skills/training-scripts/scripts/inspect_cleanrl_script.py cleanrl/ppo.py --format markdown
python sub-skills/training-scripts/scripts/build_tiny_run_command.py classic-ppo
```

Run help checks before training when optional extras may be missing. For replay-buffer algorithms, tiny training commands must keep `learning_starts < total_timesteps` and `batch_size <= buffer_size`.
