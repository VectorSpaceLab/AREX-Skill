---
name: environments
description: "Create, configure, step, validate, and wrap standardized robosuite
  manipulation envs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---
# Environments

Use this sub-skill for standardized `robosuite` manipulation envs, including `suite.make`, `MujocoEnv`, `RobotEnv`, `Lift`, `TwoArmLift`, and the other registered task envs.

## Use this sub-skill for
- selecting `env_name`, `robots`, `env_configuration`, and `gripper_types`
- creating single-arm and two-arm envs
- reading `action_spec` / `action_dim`
- choosing `use_object_obs` vs `use_camera_obs`
- understanding rewards, `horizon`, `ignore_done`, and `seed`
- using `GymWrapper`
- running safe random-policy smoke loops

## Do not use this sub-skill for
- controller internals and action-vector composition → `../controllers`
- rendering backend or pixel troubleshooting → `../rendering`
- teleoperation or demo capture → `../teleoperation`
- custom env/model creation

## Start here
- `references/api-reference.md`
- `references/observations-and-rewards.md`
- `references/workflows.md`
- `references/troubleshooting.md`

## Bundled scripts
- `scripts/run_random_policy.py` — small random rollout with action/observation summaries
- `scripts/gym_wrapper_smoke.py` — Lift/Panda GymWrapper smoke step

## Notes
- Optional capabilities such as `robosuite_models`, `mink`, HID devices, `usd-core`, Isaac/Omniverse, and on-screen display are environment-dependent.
- Keep the core standardized env workflows working without those optional pieces.

## Related sub-skills
- `../controllers`
- `../rendering`
- `../teleoperation`
