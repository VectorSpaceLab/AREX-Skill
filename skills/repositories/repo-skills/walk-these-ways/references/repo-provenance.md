# Repository provenance

Schema: `disco.repo-provenance.v1`

This file records the source snapshot used to distill the runtime skill. It is
not a claim that the current checkout or every optional backend remains
unchanged.

- Repository: `Improbable-AI/walk-these-ways`
- Remote: `https://github.com/Improbable-AI/walk-these-ways.git`
- Source commit: `0e7236bdc81ce855cbe3d70345a7899452bdeb1c`
- Branch at inspection: `master`
- Source commit subject: `add entrypoint.sh and fix headless graphics_device_id`
- Source checkout state at inspection: generated `skills/` tree was untracked;
  the source commit itself was clean before skill artifacts were added.
- Python distribution: `go1_gym==1.0.0`
- Construction scope: static/API/configuration, policy tensor and checkpoint
  contracts, actuator data/model checks, and deployment planning.
- Required backends not available for runtime verification: Isaac Gym Preview 4
  for simulator/training/playback; Unitree Go1 plus matching SDK/LCM/network for
  physical actuation.

## Relative evidence map

The distilled claims were checked against these source-relative paths:

- `README.md`
- `setup.py`
- `go1_gym/envs/go1/go1_config.py`
- `go1_gym/envs/go1/velocity_tracking/__init__.py`
- `go1_gym/envs/base/base_task.py`
- `go1_gym/envs/base/legged_robot.py`
- `go1_gym/envs/base/legged_robot_config.py`
- `go1_gym/envs/wrappers/history_wrapper.py`
- `go1_gym/envs/rewards/corl_rewards.py`
- `go1_gym_learn/ppo_cse/actor_critic.py`
- `go1_gym_learn/ppo_cse/ppo.py`
- `go1_gym_learn/ppo_cse/rollout_storage.py`
- `scripts/train.py`
- `scripts/play.py`
- `scripts/actuator_net/utils.py`
- `scripts/actuator_net/train.py`
- `scripts/actuator_net/eval.py`
- `go1_gym_deploy/scripts/deploy_policy.py`
- `go1_gym_deploy/envs/lcm_agent.py`
- `go1_gym_deploy/envs/history_wrapper.py`
- `go1_gym_deploy/utils/deployment_runner.py`
- `go1_gym_deploy/utils/command_profile.py`
- `go1_gym_deploy/utils/cheetah_state_estimator.py`
- `go1_gym_deploy/utils/network_config_unitree.py`
- `go1_gym_deploy/utils/logger.py`
- `go1_gym_deploy/docker/`
- `go1_gym_deploy/installer/`

The generated skill intentionally adapts safe validators and diagnostics rather
than copying source-relative launchers, robot binaries, model weights, logs,
Docker installers, or transfer scripts.
