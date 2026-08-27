# Go1 configuration reference

This reference records the field names and literal defaults visible in the
bundled repository evidence. It is a static reference; it does not import
`isaacgym` or prove that a setting can be executed on this host.

## Configuration order

Apply changes in this order so dimensions and derived values stay coherent:

1. Start with the `Cfg` class and decide whether the request is for the base
   defaults or the Go1 specialization. `config_go1(Cfg)` mutates the supplied
   `Cfg`/`Meta` object in place; apply it before Go1-specific overrides.
2. Set `env.num_envs`, `env.num_actions`, observation flags, privileged flags,
   `env.num_observations`, `env.num_scalar_observations`, and
   `env.num_privileged_obs` together. Recompute the concatenated observation
   size after every flag change.
3. Set `sim.dt`, `sim.use_gpu_pipeline`, `control.control_type`,
   `control.action_scale`, `control.hip_scale_reduction`, and
   `control.decimation`. The policy timestep is
   `control.decimation * sim.dt`.
4. Set the asset contract and verify the URDF, all mesh references, and any
   actuator-network file required by the selected control type.
5. Set command ranges and `num_commands`, then set gait/command observation
   flags. Keep the command index map below synchronized with reward terms.
6. Choose terrain `mesh_type`, terrain dimensions/proportions, curriculum and
   height measurement behavior. `plane`, `heightfield`, and `trimesh` take
   different simulator paths; `none` cannot support height measurement.
7. Set domain-randomization switches and ranges, then reward coefficients and
   clipping policy. Nonzero reward names must have a matching
   `_reward_<name>` method.
8. Run the safe static validator and asset diagnostic. Only on a separate
   Isaac Gym Preview 4 host should a user construct the environment or run a
   simulator test.

## Dimensions and effective Go1 defaults

`Cfg.env` declares these base values:

| Field | Base `Cfg` value | Go1 `config_go1` value/effect |
|---|---:|---|
| `num_envs` | `4096` | `4000` |
| `num_observations` | `235` | `42` |
| `num_scalar_observations` | `42` | unchanged at `42` |
| `num_privileged_obs` | `18` | unchanged at `18` |
| `num_actions` | `12` | unchanged at `12` |
| `num_observation_history` | `15` | unchanged at `15` |
| `episode_length_s` | `20` | unchanged |
| `observe_command` | `True` | unchanged |
| `observe_vel` | `True` | `False` |
| `observe_yaw` | `False` | unchanged |
| `observe_clock_inputs` | `False` | unchanged |
| `observe_two_prev_actions` | `False` | unchanged |
| `observe_gait_commands` | `False` | unchanged |

Thus the intended simple Go1 policy interface is **12 actions, 42 actor
observations, and 18 declared privileged observations**. The base class's
`235` is not the effective Go1 observation count.

The 42-dimensional Go1 actor observation is explained by the current
concatenation order: projected gravity (3), three command values (3), twelve
joint-position errors (12), twelve joint velocities (12), and twelve previous
actions (12). This assumes `observe_command=True`, `num_commands=3`, and
`observe_vel=False`; changing any flag invalidates the arithmetic unless the
configured count is changed too.

There is an important static consistency warning: with the literal default
privileged flags, the visible observation builder appends friction (1),
restitution (1), base mass (1), and COM displacement (3), while
`num_privileged_obs` remains 18. Several declared privileged flags are not
consumed by that builder. The builder asserts exact equality at runtime. Treat
`18` as the declared interface and validate the actual enabled branches on an
Isaac Gym-equipped revision before training or loading a policy. Do not hide
this mismatch by claiming that the host has executed the assertion.

## Go1 control and asset contract

`config_go1` changes the control surface to:

| Field | Go1 value | Meaning |
|---|---:|---|
| `control.control_type` | `'P'` | position target followed by PD torque calculation |
| `control.stiffness` | `{'joint': 20.}` | N*m/rad; substring matching applies to joint names |
| `control.damping` | `{'joint': 0.5}` | N*m*s/rad |
| `control.action_scale` | `0.25` | target = default joint angle + scaled action |
| `control.hip_scale_reduction` | `0.5` | additionally scales action indices 0, 3, 6, and 9 |
| `control.decimation` | `4` | four physics updates per policy action |

The action tensor is expected to have shape `[num_envs, 12]`. Actions are
clipped by `normalization.clip_actions` (base default `100.`), scaled, and
then converted to targets. The environment clips the resulting torques to
URDF-derived limits. Actuator-network behavior is outside this module's
responsibility; route it to `actuator-network`.

The Go1 asset fields set by `config_go1` are:

| Field | Value |
|---|---|
| `asset.file` | `{MINI_GYM_ROOT_DIR}/resources/robots/go1/urdf/go1.urdf` |
| `asset.foot_name` | `"foot"` |
| `asset.penalize_contacts_on` | `["thigh", "calf"]` |
| `asset.terminate_after_contacts_on` | `["base"]` |
| `asset.self_collisions` | `0` |
| `asset.flip_visual_attachments` | `False` |
| `asset.fix_base_link` | `False` |

The loader formats `MINI_GYM_ROOT_DIR`, splits the result into an asset root
and filename, and passes the remaining `asset.*` fields to Isaac Gym asset
options. The URDF's relative mesh contract includes the Go1 meshes under
`resources/robots/go1/meshes/`; the read-only runtime diagnostic checks the
known files and parses URDF mesh references. The actuator file
`resources/actuator_nets/unitree_go1.pt` is needed only when
`control.control_type == "actuator_net"`.

## Commands and gait indices

The base `commands.num_commands` is `3`. The command tensor uses these indices
when the corresponding dimensions are enabled:

| Index | Name | Typical source/range |
|---:|---|---|
| 0 | linear x velocity | `lin_vel_x` |
| 1 | linear y velocity | `lin_vel_y` |
| 2 | yaw angular velocity | `ang_vel_yaw` |
| 3 | body-height/jump command | `body_height_cmd` or jump logic |
| 4 | gait frequency | `gait_frequency_cmd_range` |
| 5 | gait phase | `gait_phase_cmd_range` |
| 6 | gait offset | `gait_offset_cmd_range` |
| 7 | gait bound | `gait_bound_cmd_range` |
| 8 | gait duration | `gait_duration_cmd_range` |
| 9 | foot-swing height | `footswing_height_range` |
| 10 | body pitch | `body_pitch_range` |
| 11 | body roll | `body_roll_range` |
| 12 | stance width | `stance_width_range` |
| 13 | stance length | `stance_length_range` |
| 14 | auxiliary reward coefficient | `aux_reward_coef_range` |

The environment's `commands_scale` follows the same order. Gait timing uses
`commands[:, 4:9]`: frequency, phase, offset, bound, and duration. The four
raw foot phase expressions are, in order, `gait+phase+offset+bound`,
`gait+offset`, `gait+bound`, and `gait+phase`; they are assigned to FL, FR,
RL, and RR desired-contact channels. `pacing_offset` changes the second and
third expressions. `gaitwise_curricula` maps categories to pronk, trot, pace,
and bound phase conventions. `observe_gait_commands`, clock inputs, or a
larger `num_commands` must be enabled deliberately; they do not appear in the
simple 42-dimensional Go1 observation.

## Terrain surface

Base terrain fields and defaults include:

- `mesh_type='trimesh'`, `horizontal_scale=0.1`, `vertical_scale=0.005`,
  `border_size=0`, `curriculum=True`, and `measure_heights=True`.
- `terrain_length=8.`, `terrain_width=8.`, `num_rows=10`, `num_cols=20`,
  `difficulty_scale=1.`, `max_platform_height=0.2`.
- `terrain_proportions=[0.1, 0.1, 0.35, 0.25, 0.2]`,
  `terrain_smoothness=0.005`, `terrain_noise_magnitude=0.1`, and
  `slope_treshold=0.75`.
- Height sample points are `measured_points_x` from `-0.8` through `0.8` at
  `0.1` increments and `measured_points_y` from `-0.5` through `0.5` at `0.1`
  increments. Height measurement therefore creates a 17-by-11 grid when
  enabled.

`config_go1` sets `mesh_type='trimesh'`, `measure_heights=False`,
`terrain_noise_magnitude=0.0`, `teleport_robots=True`, `border_size=50`,
`terrain_proportions=[0,0,0,0,0,0,0,0,1.0]`, and `curriculum=False`. For
`heightfield` or `trimesh`, `Terrain` builds a map from rows and columns and
sets environment origins. For `plane`, friction and restitution are applied
to a ground plane; for `none`, no ground mesh is created and height queries
are invalid.

## Domain randomization surface

Base switches/ranges include:

- rigid properties: `randomize_rigids_after_start=True`,
  `randomize_friction=True`, `friction_range=[0.5,1.25]`,
  `randomize_restitution=False`, `restitution_range=[0,1.0]`;
- body: `randomize_base_mass=False`, `added_mass_range=[-1.,1.]`,
  `randomize_com_displacement=False`, `com_displacement_range=[-0.15,0.15]`;
- motors: `randomize_motor_strength=False`, `motor_strength_range=[0.9,1.1]`,
  `randomize_Kp_factor=False`, `Kp_factor_range=[0.8,1.3]`,
  `randomize_Kd_factor=False`, `Kd_factor_range=[0.5,1.5]`;
- time-varying effects: `randomize_gravity=False`, `gravity_range=[-1.,1.]`,
  `gravity_rand_interval_s=7`, `gravity_impulse_duration=1.0`,
  `push_robots=True`, `push_interval_s=15`, `max_push_vel_xy=1.`,
  `randomize_lag_timesteps=True`, and `lag_timesteps=6`;
- `rand_interval_s=10` controls property refresh timing.

`config_go1` enables base-mass randomization with `added_mass_range=[-1,3]`,
friction with `[0.05,4.5]`, restitution with `[0.0,1.0]`, COM displacement
with `[-0.1,0.1]`, and motor strength with `[0.9,1.1]`; it disables pushes,
leaves Kp/Kd factor randomization false, and changes `rand_interval_s` to `6`.
The function also assigns `domain_rand.restitution=0.5`, although that field is
not declared in the base `domain_rand` class and the terrain's declared
restitution remains a separate field. Treat that assignment as a compatibility
point to verify rather than as a guaranteed simulator setting.

Privileged fields such as `priv_observe_friction`,
`priv_observe_restitution`, `priv_observe_base_mass`,
`priv_observe_com_displacement`, `priv_observe_motor_strength`, and
`priv_observe_motor_offset` must be kept aligned with the values exposed by
`compute_observations`; see the dimension warning above.

## Rewards and normalization

The base reward container is `CoRLRewards`. `reward_scales` contains the
following surface (zero values are still valid field names but are removed
from the active function list):

- tracking: `tracking_lin_vel=1.0`, `tracking_ang_vel=0.5`,
  `tracking_lin_vel_lat=0.`, `tracking_lin_vel_long=0.`;
- motion penalties: `lin_vel_z=-2.`, `ang_vel_xy=-0.05`, `orientation=-0.`,
  `torques=-0.00001`, `dof_vel=-0.`, `dof_acc=-2.5e-7`, `base_height=-0.`,
  `action_rate=-0.01`;
- contacts and gait: `feet_air_time=1.0`, `collision=-1.`,
  `feet_stumble=-0.`, `tracking_contacts=0.`,
  `tracking_contacts_shaped=0.`, `tracking_contacts_shaped_force=0.`,
  `tracking_contacts_shaped_vel=0.`, `feet_contact_forces=0.`,
  `feet_slip=0.`, `feet_clearance_cmd_linear=0.`;
- optional terms: `termination=-0.`, `jump=0.`, `energy=0.`,
  `energy_expenditure=0.`, `survival=0.`, `dof_pos_limits=0.`, `dof_pos=0.`,
  `action_smoothness_1=0.`, `action_smoothness_2=0.`, `base_motion=0.`,
  `feet_impact_vel=0.`, and `raibert_heuristic=0.`.

`config_go1` changes `torques=-0.0001`, `action_rate=-0.01`,
`dof_pos_limits=-10.0`, `orientation=-5.`, and `base_height=-30.`; it also
sets `rewards.soft_dof_pos_limit=0.9` and `rewards.base_height_target=0.34`.
The reward preparation removes zero scales and multiplies active scales by
`dt`; an active name without a matching method is warned about rather than
silently implemented. `rewards.only_positive_rewards=True` clips the total
before the termination term by default, while
`only_positive_rewards_ji22_style=False` selects the alternate path only when
enabled.

Normalization defaults are `clip_observations=100.`, `clip_actions=100.`,
`obs_scales.lin_vel=2.`, `ang_vel=0.25`, `dof_pos=1.`, and `dof_vel=0.05`.
The environment adds configured uniform observation noise when
`noise.add_noise=True`; the noise vector is hand-built for the enabled
observation flags and therefore must be reconsidered after changing shape.

## Observation history implications

`HistoryWrapper` stores `env.cfg.env.num_observation_history` consecutive
actor observations. It allocates:

`obs_history.shape == [num_envs, num_observation_history * env.num_obs]`

With Go1's declared `num_observation_history=15` and effective
`num_obs=42`, this is `[num_envs, 630]`. `reset()` zeroes the complete history;
`step()` drops the oldest 42 values and appends the latest observation.
Privileged observations are returned separately and are not concatenated into
this history. If `num_observations`, a command flag, or history length changes,
update the learner's expected history dimension and the declared privileged
size together. A reset-history shape can look correct even while the
privileged-observation assertion would fail later, so validate both surfaces.
