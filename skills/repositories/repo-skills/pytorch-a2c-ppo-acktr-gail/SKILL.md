---
name: pytorch-a2c-ppo-acktr-gail
description: "Operate the PyTorch A2C/PPO/ACKTR/GAIL reinforcement-learning
  repository, including training commands, model components, GAIL demos, and
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# pytorch-a2c-ppo-acktr-gail

Use this repo skill when a task involves the PyTorch implementation of A2C, PPO, ACKTR, and GAIL reinforcement-learning workflows, including Gym environment setup, training command construction, policy/rollout internals, checkpoint playback, or imitation-learning expert data.

## Start Here

- Confirm the source/version baseline before relying on the skill: [references/repo-provenance.md](references/repo-provenance.md).
- For package install, import, dependency, Gym/PyBullet, CUDA, and stale-flag issues, read [references/troubleshooting.md](references/troubleshooting.md).
- For shared parser flags, command conventions, and source-script mapping, read [references/cli-and-config-reference.md](references/cli-and-config-reference.md).
- For checkpoints, monitor logs, historical result artifacts, and expert-data artifacts, read [references/data-and-artifacts.md](references/data-and-artifacts.md).
- Run [scripts/check_install.py](scripts/check_install.py) for a safe import/API smoke check after installing the package.

## Sub-skill Routes

| Task | Load |
| --- | --- |
| Build or debug A2C/PPO/ACKTR training commands, evaluation intervals, checkpoint playback, Gym environment wrappers, or long-run experiment settings. | [sub-skills/training-workflows/SKILL.md](sub-skills/training-workflows/SKILL.md) |
| Inspect or modify `Policy`, `CNNBase`, `MLPBase`, distributions, `RolloutStorage`, `A2C_ACKTR`, `PPO`, KFAC, schedules, or tensor-shape behavior. | [sub-skills/model-components/SKILL.md](sub-skills/model-components/SKILL.md) |
| Convert expert demonstrations, validate GAIL HDF5/`.pt` formats, use `ExpertDataset`, or explain `Discriminator`/`--gail` behavior. | [sub-skills/gail-imitation/SKILL.md](sub-skills/gail-imitation/SKILL.md) |

## Minimal Public Setup

This is an older Gym/PyTorch codebase. A practical environment needs the package, PyTorch, Gym, Stable-Baselines3 wrapper utilities, PyBullet support if using Bullet envs, Matplotlib, and `h5py` for GAIL files.

```bash
pip install -e .
pip install h5py
python - <<'PY'
import a2c_ppo_acktr
from a2c_ppo_acktr.model import Policy
from a2c_ppo_acktr.storage import RolloutStorage
print('import ok')
PY
```

If `pybullet_envs` fails with a Gym registry error, read [references/troubleshooting.md](references/troubleshooting.md#gym--pybullet-registry-failure) before changing training code.

## Safe Verification First

Do not start full Atari, MuJoCo, PyBullet, or GAIL training just to verify the setup. Prefer:

```bash
python scripts/check_install.py
python sub-skills/training-workflows/scripts/build_training_command.py --preset atari-ppo --env-name PongNoFrameskip-v4
python sub-skills/model-components/scripts/smoke_model_components.py
python sub-skills/gail-imitation/scripts/convert_gail_h5_to_pt.py --help
```

Only run long training after the user confirms the target environment, simulator dependencies, data availability, compute budget, and output directories.
