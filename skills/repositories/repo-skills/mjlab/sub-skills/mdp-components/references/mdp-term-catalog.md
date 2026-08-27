# MDP term catalog

This catalog names the installed term families and their intended use. Inspect
live signatures with the bundled `inspect_mdp_terms.py` helper before writing a
large config.

## Observations

Common functions under `mjlab.envs.mdp.observations`:

- `base_lin_vel`, `base_ang_vel`: root velocities.
- `projected_gravity`: gravity vector in the base frame.
- `joint_pos_rel`, `joint_vel_rel`: joint state relative to default or current
  references.
- `last_action`: previous policy command.
- `generated_commands`: command tensor by name.
- `builtin_sensor`, `projected_gravity_from_sensor`, `height_scan`: sensor-fed
  observations.

## Rewards

Common functions under `mjlab.envs.mdp.rewards`:

- `is_alive`, `is_terminated`: survival/failure shaping.
- `joint_torques_l2`, `joint_vel_l2`, `joint_acc_l2`: smoothness/energy
  penalties.
- `action_rate_l2`, `action_acc_l2`: action smoothness.
- `joint_pos_limits`: soft joint-limit penalty.
- `posture`: posture target penalty.
- `electrical_power_cost`: actuator power proxy.
- `flat_orientation_l2`: uprightness penalty.

Use negative weights for penalties and positive weights for rewards. Remember
that environment configs usually scale reward values by step dt.

## Terminations

Common functions under `mjlab.envs.mdp.terminations`:

- `time_out`: marks time-limit truncation when configured with `time_out=True`.
- `bad_orientation`: terminates when orientation exceeds a threshold.
- `root_height_below_minimum`: catches falls.
- `nan_detection`: stops environments with invalid state.

## Events

Common functions under `mjlab.envs.mdp.events`:

- `reset_scene_to_default`: default reset behavior.
- `reset_root_state_uniform`: randomize root pose/velocity.
- `reset_root_state_from_flat_patches`: place roots on sampled terrain patches.
- `reset_joints_by_offset`: perturb joint initial state.
- `push_by_setting_velocity`, `apply_external_force_torque`,
  `apply_body_impulse`: perturb robot/object motion.
- `randomize_terrain`: refresh terrain curriculum/assignment.

Events require an `EventTermCfg` mode. Step and interval events should be
lightweight enough for training-scale environments.

## Domain randomization helpers

Runtime model-field randomization lives under `mjlab.envs.mdp.dr`. Families
include body, geom, joint/dof, actuator, camera, light, material, site, tendon,
and pair fields. Use the perception/terrain/randomization sub-skill for deeper
field-expansion and recompute guidance.

## Metrics and curricula

- `mean_action_acc`: simple diagnostic metric.
- Reward curriculum and termination curriculum classes adjust term weights or
  parameters based on training progress.
- Task-family curricula can adjust velocity command ranges or terrain levels.

## Wiring reminder

Every callable listed here still needs the right manager config object and
params. For example, a reward function is not active until wrapped in
`RewardTermCfg(func=..., weight=..., params=...)` and placed in the
`rewards` dictionary.
