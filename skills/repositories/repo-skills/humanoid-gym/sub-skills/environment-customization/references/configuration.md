# Configuration reference

Evidence used: `README.md` code structure and add-a-new-environment sections, `humanoid/envs/base/base_config.py`, `humanoid/envs/base/legged_robot_config.py`, `humanoid/envs/custom/humanoid_config.py`, `humanoid/utils/helpers.py`, and the installed inspection notes.

## Inheritance model

- `BaseConfig` recursively instantiates nested classes.
- The configs are mutable objects; create fresh instances for new tasks instead of editing the baseline registration in place.
- `class_to_dict(obj)` recursively serializes nested config objects for `task_registry` and sim-parameter parsing.
- `update_cfg_from_args(env_cfg, cfg_train, args)` only overrides `env_cfg.env.num_envs`, `cfg_train.seed`, `cfg_train.runner.max_iterations`, `cfg_train.runner.resume`, `cfg_train.runner.experiment_name`, `cfg_train.runner.run_name`, `cfg_train.runner.load_run`, and `cfg_train.runner.checkpoint`.

## Base legged defaults

| Field | Value | Notes |
|---|---:|---|
| `LeggedRobotCfg.env.num_envs` | 4096 | Default parallel rollout count |
| `LeggedRobotCfg.env.num_observations` | 235 | Base legged observation layout |
| `LeggedRobotCfg.env.num_privileged_obs` | `None` | No critic-only observations by default |
| `LeggedRobotCfg.env.num_actions` | 12 | Matches the XBot-L actuator count |
| `LeggedRobotCfg.env.episode_length_s` | 20 | Base episode horizon |
| `LeggedRobotCfg.terrain.mesh_type` | `trimesh` | Rough-terrain default in the base config |
| `LeggedRobotCfg.terrain.measure_heights` | `True` | Base terrain wants height samples |
| `LeggedRobotCfg.control.action_scale` | 0.5 | Base PD action scaling |
| `LeggedRobotCfg.control.decimation` | 4 | Base policy-to-sim ratio |
| `LeggedRobotCfg.sim.dt` | 0.005 | Base simulation step |
| `LeggedRobotCfgPPO.runner.experiment_name` | `test` | Base training log root |
| `LeggedRobotCfgPPO.runner.num_steps_per_env` | 24 | Base rollout length |
| `LeggedRobotCfgPPO.runner.max_iterations` | 1500 | Base PPO iteration budget |

## XBot-L overrides

### Environment and stacks

- `frame_stack=15`
- `c_frame_stack=3`
- `num_single_obs=47`
- `num_observations=705`
- `single_num_privileged_obs=73`
- `num_privileged_obs=219`
- `num_actions=12`
- `episode_length_s=24`
- `use_ref_actions=False`

Derived facts:

- policy input stack = `15 x 47 = 705`
- critic stack = `3 x 73 = 219`
- policy time step = `sim.dt * control.decimation = 0.001 * 10 = 0.01 s`

### Asset layout and naming

- `asset.file='{LEGGED_GYM_ROOT_DIR}/resources/robots/XBot/urdf/XBot-L.urdf'`
- `asset.name='XBot-L'`
- `asset.foot_name='ankle_roll'`
- `asset.knee_name='knee'`
- `asset.terminate_after_contacts_on=['base_link']`
- `asset.penalize_contacts_on=['base_link']`
- `asset.fix_base_link=False`
- `asset.replace_cylinder_with_capsule=False`
- `asset.flip_visual_attachments=False`

The URDF non-fixed joint names are the 12 leg joints only:

- `left_leg_roll_joint`
- `left_leg_yaw_joint`
- `left_leg_pitch_joint`
- `left_knee_joint`
- `left_ankle_pitch_joint`
- `left_ankle_roll_joint`
- `right_leg_roll_joint`
- `right_leg_yaw_joint`
- `right_leg_pitch_joint`
- `right_knee_joint`
- `right_ankle_pitch_joint`
- `right_ankle_roll_joint`

These asset-name fields are substring filters, not exact matches. On XBot-L, `ankle_roll` matches the two ankle-roll links, while `knee` and `base_link` match multiple related bodies because the asset includes motor/linkage and upper-body link names that contain those substrings.

### Terrain and motion

- `terrain.mesh_type='plane'`
- `terrain.curriculum=False`
- `terrain.measure_heights=False`
- `terrain.static_friction=0.6`
- `terrain.dynamic_friction=0.6`
- `terrain.terrain_length=8.0`
- `terrain.terrain_width=8.0`
- `terrain.num_rows=20`
- `terrain.num_cols=20`
- `terrain.terrain_proportions=[0.2, 0.2, 0.4, 0.1, 0.1, 0, 0]`
- `commands.resampling_time=8.0`
- `commands.heading_command=True`
- `commands.ranges.lin_vel_x=[-0.3, 0.6]`
- `commands.ranges.lin_vel_y=[-0.3, 0.3]`
- `commands.ranges.ang_vel_yaw=[-0.3, 0.3]`
- `commands.ranges.heading=[-3.14, 3.14]`

### Control, sim, noise, and randomization

- `control.stiffness={'leg_roll': 200.0, 'leg_pitch': 350.0, 'leg_yaw': 200.0, 'knee': 350.0, 'ankle': 15}`
- `control.damping={'leg_roll': 10, 'leg_pitch': 10, 'leg_yaw': 10, 'knee': 10, 'ankle': 10}`
- `control.action_scale=0.25`
- `control.decimation=10`
- `sim.dt=0.001`
- `sim.substeps=1`
- `sim.up_axis=1`
- `domain_rand.randomize_friction=True`
- `domain_rand.friction_range=[0.1, 2.0]`
- `domain_rand.randomize_base_mass=True`
- `domain_rand.added_mass_range=[-5.0, 5.0]`
- `domain_rand.push_robots=True`
- `domain_rand.push_interval_s=4`
- `domain_rand.max_push_vel_xy=0.2`
- `domain_rand.max_push_ang_vel=0.4`
- `domain_rand.action_delay=0.5`
- `domain_rand.action_noise=0.02`
- `noise.add_noise=True`
- `noise.noise_level=0.6`
- `normalization.clip_observations=18.0`
- `normalization.clip_actions=18.0`

### Rewards and normalization

- `rewards.base_height_target=0.89`
- `rewards.min_dist=0.2`
- `rewards.max_dist=0.5`
- `rewards.target_joint_pos_scale=0.17`
- `rewards.target_feet_height=0.06`
- `rewards.cycle_time=0.64`
- `rewards.only_positive_rewards=True`
- `rewards.tracking_sigma=5`
- `rewards.max_contact_force=700`
- `normalization.obs_scales.lin_vel=2.0`
- `normalization.obs_scales.ang_vel=1.0`
- `normalization.obs_scales.dof_pos=1.0`
- `normalization.obs_scales.dof_vel=0.05`
- `normalization.obs_scales.quat=1.0`
- `normalization.obs_scales.height_measurements=5.0`

### PPO runner

- `runner_class_name='OnPolicyRunner'`
- `seed=5`
- `policy.init_noise_std=1.0`
- `policy.actor_hidden_dims=[512, 256, 128]`
- `policy.critic_hidden_dims=[768, 256, 128]`
- `algorithm.entropy_coef=0.001`
- `algorithm.learning_rate=1e-5`
- `algorithm.num_learning_epochs=2`
- `algorithm.gamma=0.994`
- `algorithm.lam=0.9`
- `algorithm.num_mini_batches=4`
- `runner.policy_class_name='ActorCritic'`
- `runner.algorithm_class_name='PPO'`
- `runner.num_steps_per_env=60`
- `runner.max_iterations=3001`
- `runner.save_interval=100`
- `runner.experiment_name='XBot_ppo'`

## Practical edit rule

When creating a new humanoid variant, prefer a subclass that overrides only the changed nested classes. That keeps the baseline `humanoid_ppo` config stable and makes config diffing much easier.
