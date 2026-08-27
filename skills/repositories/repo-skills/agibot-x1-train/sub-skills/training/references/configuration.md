# X1 DH configuration and invariants

## Registered config objects

`humanoid/envs/__init__.py` registers exactly:

```text
x1_dh_stand -> X1DHStandEnv, X1DHStandCfg(), X1DHStandCfgPPO()
```

`BaseConfig` recursively instantiates nested config classes. `class_to_dict`
then turns the instantiated objects into dictionaries for the runner. The
registry copies the PPO seed into the environment config before applying CLI
overrides. The effective config is therefore a mutable object, not a YAML file;
inspect it before editing and keep related dimensions synchronized.

## Observation and action contract

The X1 task config is internally dimensioned as follows:

| Field | Value | Meaning |
| --- | ---: | --- |
| `env.num_envs` | 4096 | parallel Isaac Gym environments; override with `--num_envs` |
| `env.num_actions` | 12 | six leg joints per side |
| `env.num_single_obs` | 47 | one actor observation frame |
| `env.frame_stack` | 66 | long history frames |
| `env.num_observations` | 3102 | `66 * 47`, actor input |
| `env.short_frame_stack` | 5 | short history frames |
| `env.num_short_obs` (derived) | 235 | `5 * 47`, estimator/actor short input |
| `env.single_num_privileged_obs` | 73 | one critic frame |
| `env.c_frame_stack` | 3 | privileged critic history frames |
| `env.num_privileged_obs` | 219 | `3 * 73`, critic input |
| `env.single_linvel_index` | 53 | index within one privileged frame |
| `env.single_linvel_index` in critic | 199 | `73 * (3 - 1) + 53` when heights are off |
| `env.num_commands` | 5 | command-related observation width |
| `commands.num_commands` | 4 | raw command storage width |

The 47 actor features are:

```text
5 command_input (sin phase, cos phase, scaled vx, scaled vy, scaled yaw)
12 q = lagged dof position - default dof position
12 dq = lagged dof velocity
12 previous/current action buffer
3 lagged base angular velocity
3 lagged base Euler angles
```

The 73 privileged features are:

```text
5 command_input
12 dof position relative to default PD target
12 dof velocity
12 actions
12 dof position error to gait reference
3 base linear velocity
3 base angular velocity
3 base Euler angles
2 random push xy velocity
3 random push angular velocity
1 environment friction
1 fixed-link body mass / 10
2 stance mask
2 foot contact mask
```

If `terrain.measure_heights` is later enabled, the privileged frame gains
`terrain.num_height` values and the critic dimension and `lin_vel_idx` must be
recomputed. The X1 default has `measure_heights=False`, so do not add height
features to the 219-wide critic by assumption.

`ActorCriticDH` reshapes the long actor input as `(-1, 66, 47)` for its
`Conv1d`. With `kernel_size=[6,4]`, `filter_size=[32,16]`, and
`stride_size=[3,2]`, the temporal widths are 47 -> 14 -> 6 and the flattened
CNN width is `16 * 6 = 96`; the CNN output is 64. Its actor MLP input is
`235 + 64 + 3 = 302`, because the state estimator produces a 3-vector. Its
critic input is 219 and its output is one value. The policy output and action
noise vector are both 12 wide.

Do not casually change one of `num_single_obs`, `frame_stack`,
`short_frame_stack`, CNN kernels/strides, `in_channels`, or `lh_output_dim`.
Every such change affects environment buffers, `view(-1, in_channels,
num_proprio_obs)`, the first actor layer, estimator input, and checkpoint
compatibility.

## Simulation, control, and reset assumptions

- Initial base position is `[0, 0, 0.7]`; the default 12 joint angles are
  explicitly defined in the X1 config and are the target when action is zero.
- Control is position PD (`control_type='P'`): target is
  `action_scale * action + default_dof_pos` with `action_scale=0.5`.
  Simulation `dt=0.001` and `decimation=10`, so policy/environment `dt` is
  0.01 seconds (100 Hz); the PhysX simulation runs at 1000 Hz.
- Safety factors are position 1.0, velocity 1.0, and torque 0.85. Actual
  URDF limits are loaded by the native environment and then scaled; torque
  output is clipped to those loaded limits.
- The asset is the X1 URDF, uses `ankle_roll` feet and `knee_pitch` knee body
  matching, terminates and penalizes contacts on `base_link`, and enables
  trimesh terrain with 20 rows and 20 columns. Native asset/terrain behavior
  cannot be validated without Isaac Gym Preview 4.
- Episode length is 24 seconds, hence approximately 2400 policy steps from
  `ceil(24 / 0.01)`. Resets clear action/state histories, randomize initial
  DOF positions around defaults by ±0.1, choose a gait phase start of 0 or
  0.5, regenerate gait schedule, and resample commands.
- Normalization uses linear velocity 2, angular velocity 1, DOF position 1,
  DOF velocity 0.05, quaternion 1, and height 5; observation and action clips
  are 100. Observation noise is enabled at level 1.5 with task-specific
  position/velocity/velocity-orientation scales.

## Commands and gait schedule

The raw command storage has four fields: `lin_vel_x`, `lin_vel_y`,
`ang_vel_yaw`, and `heading`. This task disables heading mode, so resampling
writes the first three and leaves heading unused. The observation uses the
three velocity fields after `commands_scale=[2,2,1]`, preceded by gait phase
sine/cosine. A command with velocity norm at or below `stand_com_threshold`
(0.05) is a stand command.

The task uses command curriculum (`max_curriculum=1.5`) and a 25-second nominal
resampling time, but `X1DHStandEnv` overrides the base time-based callback with
a gait-segment callback. Its gait list is:

```text
["walk_omnidirectional", "stand", "walk_omnidirectional"]
```

Each segment's random duration is drawn from its configured range:

```text
walk_omnidirectional: 4..6 s
stand:                2..3 s
walk_omnidirectional: 4..6 s
```

The generated tick boundaries are scaled to the episode length and commands
are resampled at those boundaries. Stand sets x/y and yaw (or heading in the
alternate mode) to zero; omnidirectional walk samples x in [-0.4, 1.2], y in
[-0.4, 0.4], and yaw in [-0.6, 0.6]. Rotation and sagittal/lateral helpers
exist for the broader gait API but are not in this default gait list. The
phase cycle is 0.7 seconds; stand forces phase to zero and the stance mask to
double support near phase transitions.

When constructing synthetic commands or modifying a gait, preserve the
four-field raw storage versus five-field observation distinction, keep every
name in `commands.gait` present in `gait_time_range`, and keep ranges ordered
`[min, max]`. Do not send a five-element action tensor: actions are 12 joint
values.

## Terrain, reward, and randomization assumptions

The task uses non-curriculum trimesh terrain (`curriculum=False`) with static
and dynamic friction 0.6, 8 m terrain length/width, platform 3 m, and terrain
proportions flat 0.3, rough flat 0.2, slope up 0.2, slope down 0.2, discrete
0.1, with the other listed categories at zero. Height measurements are off.
The reward target base height is 0.61 m, gait cycle 0.7 s, target swing-foot
height 0.03..0.06 m, and `only_positive_rewards=True`. Nonzero terms include
reference joint position, foot clearance/contact/air-time, foot slip/distance,
velocity tracking, orientation/height/acceleration, smoothness and energy,
stand still, collisions, and soft limit penalties. Reward scales are multiplied
by `dt` when the environment prepares them.

Important enabled randomization defaults:

- friction [0.2, 1.3], restitution [0, 0.4];
- velocity/angular pushes enabled every 4 seconds, with max xy/angular speed
  0.2 and progressive durations 0..0.25 seconds;
- base mass ±3, COM displacement ±0.05 m in each axis, link mass multiplier
  0.9..1.1;
- stiffness/damping multipliers 0.8..1.2 and torque multipliers 0.8..1.2;
- motor offsets ±0.035 rad;
- joint friction 0.01..1.15 (with joint-specific overrides), damping
  0.3..1.5, and armature 0.0001..0.05;
- Coulomb friction 0.1..0.9 and viscous friction 0.05..0.1;
- action lag enabled with randomized 5..40 ticks; DOF lag enabled with
  randomized 0..40 ticks; position/velocity-separated lag and IMU lag are
  disabled by default.

These settings are native sim assumptions, not CPU-verifiable facts. An
ablation should state which randomizers were disabled and why, then use a
fresh run name and checkpoint rather than silently reusing a robust-policy
checkpoint.

## PPO configuration

The task uses `DHOnPolicyRunner`, `ActorCriticDH`, and `DHPPO` with seed 5.
The policy has actor `[512,256,128]`, critic `[768,256,128]`, state estimator
`[256,128,64]`, long-history CNN settings above, and initial action noise 1.0.
The algorithm uses entropy coefficient 0.001, learning rate 1e-5, two learning
epochs, gamma 0.994, lambda 0.9, four mini-batches, and the base defaults for
clipping/value loss/gradient norm unless overridden. The runner uses 24 steps
per environment, 20,000 maximum iterations, and saves every 100 iterations.
