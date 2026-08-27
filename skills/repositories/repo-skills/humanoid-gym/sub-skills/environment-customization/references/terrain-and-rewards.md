# Terrain and rewards reference

Evidence used: `humanoid/envs/base/legged_robot.py`, `humanoid/envs/custom/humanoid_env.py`, `humanoid/utils/terrain.py`, `humanoid/envs/base/legged_robot_config.py`, `humanoid/utils/calculate_gait.py`, and the installed inspection notes.

## Terrain modes

| `mesh_type` | What happens | Notes |
|---|---|---|
| `plane` | Adds a ground plane | XBot-L default |
| `heightfield` | Builds `HumanoidTerrain` and adds a heightfield | Terrain data is generated from the configured proportions |
| `trimesh` | Builds `HumanoidTerrain` and adds a triangle mesh | Rough terrain branch |
| anything else | Raises a `ValueError` | Unsupported |

XBot-L ships with `terrain.mesh_type='plane'`, `terrain.curriculum=False`, and `terrain.measure_heights=False`, so the default task does not use terrain sampling at all.

`HumanoidTerrain` uses the XBot proportions `[0.2, 0.2, 0.4, 0.1, 0.1, 0, 0]`, which yields a simple mix of flat, obstacle, uniform-noise, and slope terrains. The zero entries effectively disable the later terrain bins.

## Reward discovery rule

`LeggedRobot._prepare_reward_function()` does three things:

1. drops reward scales whose value is zero,
2. multiplies all remaining reward scales by `dt`, and
3. looks up a method named `_reward_<scale_name>` for each remaining term.

`termination` is treated specially and is added after clipping.

### XBot-L reward scales and methods

| Scale name | Method | Use |
|---|---|---|
| `joint_pos` | `_reward_joint_pos` | Track the reference gait joint targets |
| `feet_distance` | `_reward_feet_distance` | Keep feet from collapsing together or spreading too far |
| `knee_distance` | `_reward_knee_distance` | Same idea for knees |
| `foot_slip` | `_reward_foot_slip` | Penalize stance-foot slip |
| `feet_air_time` | `_reward_feet_air_time` | Encourage stepping |
| `feet_contact_number` | `_reward_feet_contact_number` | Match stance/contact phase |
| `orientation` | `_reward_orientation` | Keep the torso level |
| `feet_contact_forces` | `_reward_feet_contact_forces` | Penalize large contact forces |
| `default_joint_pos` | `_reward_default_joint_pos` | Stay near the default pose |
| `base_height` | `_reward_base_height` | Track the target torso height |
| `base_acc` | `_reward_base_acc` | Keep the base smooth |
| `vel_mismatch_exp` | `_reward_vel_mismatch_exp` | Penalize unwanted vertical/lateral velocity |
| `low_speed` | `_reward_low_speed` | Keep commanded forward speed in range |
| `track_vel_hard` | `_reward_track_vel_hard` | Hard velocity tracking |
| `tracking_lin_vel` | `_reward_tracking_lin_vel` | Linear velocity tracking |
| `tracking_ang_vel` | `_reward_tracking_ang_vel` | Yaw-rate tracking |
| `feet_clearance` | `_reward_feet_clearance` | Lift the swing foot high enough |
| `torques` | `_reward_torques` | Penalize effort |
| `dof_vel` | `_reward_dof_vel` | Penalize joint speed |
| `dof_acc` | `_reward_dof_acc` | Penalize joint acceleration |
| `collision` | `_reward_collision` | Penalize body contacts |
| `action_smoothness` | `_reward_action_smoothness` | Penalize rapid action changes |

If you add or rename a reward scale, add the matching `_reward_<name>` method or set the scale to zero.

## Observation, action, and reference-action layout

`XBotLFreeEnv` stacks 15 actor observations and 3 critic observations. The layout is fixed in the env code and the noise vector must match it.

### Single actor observation: 47 dims

1. gait phase `sin` and `cos` = 2
2. command input `(vx, vy, yaw-rate)` = 3
3. relative joint positions = 12
4. joint velocities = 12
5. previous actions = 12
6. base angular velocity = 3
7. base Euler angles = 3

Total: `2 + 3 + 12 + 12 + 12 + 3 + 3 = 47`

### Single privileged observation: 73 dims

1. command input = 5
2. joint target offset = 12
3. joint velocities = 12
4. actions = 12
5. reference tracking error = 12
6. base linear velocity = 3
7. base angular velocity = 3
8. base Euler angles = 3
9. push force XY = 2
10. push torque = 3
11. friction coefficient = 1
12. body mass scalar = 1
13. stance mask = 2
14. contact mask = 2

Total: `73`

### Stack sizes

- actor stack = `15 x 47 = 705`
- critic stack = `3 x 73 = 219`

### Noise vector slices

`_get_noise_scale_vec()` assumes a 47-D single observation and uses these fixed slices:

- `0:5` commands
- `5:17` joint position noise
- `17:29` joint velocity noise
- `29:41` previous action noise
- `41:44` angular-velocity noise
- `44:47` Euler-angle noise

If you change the observation layout, update `num_single_obs`, the stack sizes, the privileged-observation sizes, and these slices together.

## Gait and reference action

- Phase is `episode_length_buf * dt / cycle_time`.
- `sin(2π phase)` drives the alternating stance/swing pattern.
- `compute_ref_state()` fills `ref_dof_pos` from that phase and the `target_joint_pos_scale`.
- `ref_action = 2 * ref_dof_pos`.
- If `use_ref_actions=True`, the reference action is added before clipping, delay, and action noise.

The bundled `scripts/solve_gait_coefficients.py` reproduces the swing-foot coefficient solve from the original helper without plotting.

## Practical editing rule

If you touch observations, reference actions, or reward terms, re-check the stack sizes, noise slices, and reward-scale names before you hand the task off.
