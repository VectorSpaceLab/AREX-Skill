---
name: humanoid-gym
description: "Guide Humanoid-Gym users through PPO training, XBot-L environment
  customization, and MuJoCo sim-to-sim deployment."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# Humanoid-Gym

Use this repo skill when a future agent needs to work with Humanoid-Gym: training or evaluating the bundled `humanoid_ppo` task, changing the XBot-L environment, or validating/exporting a policy for MuJoCo sim-to-sim.

## Read this first
- `references/repo-provenance.md` if you need to compare the current checkout against the snapshot used to build this skill.
- `references/installation-and-backends.md` for Python, torch, Isaac Gym, MuJoCo, and CUDA readiness.
- `references/troubleshooting.md` when setup, import, backend, or checkpoint selection fails.

## Main routes
- `sub-skills/training-and-evaluation/` — PPO training, evaluation, checkpoint loading, and TorchScript export.
- `sub-skills/environment-customization/` — XBot-L config, rewards, terrain, and new robot/environment setup.
- `sub-skills/sim2sim-deployment/` — MuJoCo deployment of exported policies and asset/policy validation.

## Verified package facts
- Distribution name: `humanoid`
- Version: `1.0.0`
- Registered public task in this checkout: `humanoid_ppo`
- XBot-L policy dimensions: 705 observations, 219 privileged observations, 12 actions
- The public `play.py` export path writes `logs/<experiment_name>/exported/policies/policy_1.pt`

## Minimal install and check
Use a Python 3.8 environment for the repo's documented backend stack.

1. Install this checkout in editable mode from a local clone.
2. Install the runtime stack required by the selected route.
3. Confirm `import humanoid` and `python -m pip check`.
4. If you need train/play execution, confirm Isaac Gym Preview 4 is installed and importable.

Suggested smoke check:

```bash
python -c "import humanoid; print(humanoid.LEGGED_GYM_ROOT_DIR)"
```

If Isaac Gym is missing, stay in static/command-building mode and use the bundled helpers instead of claiming native training or evaluation succeeded.

## Helper script
- `scripts/inspect_humanoid_gym_install.py` — run this when you want a safe root-level install/resource/backend summary without launching Isaac Gym.

## Notes for future agents
- `humanoid/scripts/train.py` and `humanoid/scripts/play.py` are the user-facing PPO entry points, but they require the Isaac Gym backend for real execution.
- `humanoid/scripts/play.py` exports the actor only and hard-codes render/export side effects unless the source file is edited.
- `humanoid/scripts/sim2sim.py` uses MuJoCo viewer rollout and is best validated with the bundled sim2sim sub-skill.
