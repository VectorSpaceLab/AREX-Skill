---
name: environment-customization
description: "Customize XBot-L and new humanoid environments safely: config
  inheritance, task registration, assets, observations/actions, gait reference
  actions, rewards, domain randomization, terrain modes, and new robot
  onboarding."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# environment-customization

Use this sub-skill for:
- changing `LeggedRobotCfg` / `LeggedRobotCfgPPO`-style configs
- adding a new humanoid robot or environment
- adjusting robot asset paths, body/joint names, default joint angles, PD gains
- changing observation/action layouts, stack sizes, noise vectors, or privileged obs
- tuning reward scales/functions, gait/reference action logic, and domain randomization
- switching between plane, heightfield, and trimesh terrain modes

Do not use this sub-skill for:
- PPO runner execution, training, evaluation, export, or checkpoint loading -> [`training-and-evaluation`](../training-and-evaluation/SKILL.md)
- MuJoCo sim-to-sim rollout or joint mapping -> [`sim2sim-deployment`](../sim2sim-deployment/SKILL.md)

## Bundle

Read these bundled references first:
- [`references/configuration.md`](references/configuration.md)
- [`references/task-registration.md`](references/task-registration.md)
- [`references/terrain-and-rewards.md`](references/terrain-and-rewards.md)
- [`references/troubleshooting.md`](references/troubleshooting.md)

Use these bundled scripts for safe inspection:
- [`scripts/summarize_xbot_config.py`](scripts/summarize_xbot_config.py)
- [`scripts/solve_gait_coefficients.py`](scripts/solve_gait_coefficients.py)

## Working rule

Keep `humanoid_ppo` intact. When adding a new robot or environment, create a new config/env pair and register a new task id instead of mutating the baseline task in place.

## Required consistency checks

Before handing off a customization, confirm:
- asset path resolves under `resources/robots/XBot/...` or the new robot's equivalent
- body substrings for feet, knees, base/termination contacts match the asset bodies
- every actuated joint has a `default_joint_angles` entry and a PD gain substring match
- `num_single_obs`, `frame_stack`, `num_observations`, and the noise vector agree
- `single_num_privileged_obs`, `c_frame_stack`, and `num_privileged_obs` agree
- reward scales only name functions that exist as `_reward_<name>`
- the chosen terrain mode is one of the supported branches
- runtime env instantiation remains behind the Isaac Gym backend gate

## Backend note

Static parsing and asset inspection are safe here. Any step that instantiates the Isaac Gym environment still needs Isaac Gym Preview 4; if it is unavailable, report the environment-runtime portion as `BLOCKED_REQUIRED_BACKEND` and do not claim execution passed. Full real Isaac Gym train/play native verification is routed to `training-and-evaluation` and remains `BLOCKED_REQUIRED_BACKEND` without the required backend. This drafted sub-skill is staged only; import is not being performed.
