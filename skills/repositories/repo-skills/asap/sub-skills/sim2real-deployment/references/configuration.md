# Deployment Configuration Reference

Primary config: `sim2real/config/g1_29dof_hist.yaml`.

ASAP deployment scripts expect this config to match both the robot hardware/simulator and the exported ONNX policies. Treat config edits as part of the safety-critical runtime, not as cosmetic parameters.

## Path and Working Directory Rules

Run from `sim2real/` unless you have audited every relative path:

```bash
cd sim2real
python sim_env/base_sim.py --config=config/g1_29dof_hist.yaml
python rl_policy/deepmimic_dec_loco_height.py --config=config/g1_29dof_hist.yaml \
  --loco_model_path=./models/dec_loco/20250109_231507-noDR_rand_history_loco_stand_height_noise-decoupled_locomotion-g1_29dof/model_6600.onnx \
  --mimic_model_paths=./models/mimic
```

Why this matters:

- `ROBOT_SCENE`, `ROBOT`, and `ASSET_ROOT` are relative paths such as `../humanoidverse/data/robots/g1/...`.
- Policy scripts append `./rl_policy` or `../` to `sys.path`.
- README model paths are relative to `sim2real/`.

## Robot and Asset Fields

| Field | Meaning | Notes |
| --- | --- | --- |
| `ROBOT_TYPE` | Runtime robot type used by `Robot`, `CommandSender`, `StateProcessor`, and bridge class selection. | Keep `"g1_29dof"` for the supplied G1 deployment config. `mimic_robot_types` may reference `g1_29dof_anneal_23dof`, but `CommandSender` and `StateProcessor` accept the top-level G1 runtime as `g1_29dof`. |
| `ROBOT_SCENE` | MuJoCo XML scene for sim2sim. | Default is `../humanoidverse/data/robots/g1/scene_29dof.xml`; the commented free-base scene must match `FREE_BASE`. |
| `ROBOT` | URDF path. | Used for robot metadata and should match the 29-DOF asset set. The current checkout does not ship the exact `g1_29dof.urdf` path in this config, and the inspected runtime code does not read this field directly. |
| `ASSET_ROOT` / `ASSET_FILE` | Asset root and URDF asset name. | Keep paths under `../humanoidverse/data/robots/g1` unless adding an audited robot. |
| `FREE_BASE` | Whether MuJoCo controls include a free-base actuator offset. | Default `False`; changing it affects torque vector layout in `BaseSimulator`. |
| `USE_SENSOR` | Whether sim2sim bridge reads MuJoCo sensors instead of qpos/qvel ground truth. | Default `False`; if set true, the MuJoCo XML must include expected motor and frame sensors. |

Consistency checks for G1:

- `NUM_MOTORS` and `NUM_JOINTS` should both be `29`.
- `MOTOR2JOINT`, `JOINT2MOTOR`, `DEFAULT_DOF_ANGLES`, `DEFAULT_MOTOR_ANGLES`, gain lists, and motor limits must have lengths compatible with `29` motors/joints.
- The real robot must be physically configured for 29 DOF before using this config.

## DDS, ROS2, and Network Fields

| Field | Sim2Sim default | Sim2Real default | Notes |
| --- | --- | --- | --- |
| `DOMAIN_ID` | `0` | Lab-selected DDS domain, often `0` | All processes that communicate must use the same domain. |
| `INTERFACE` | `"lo"` on Linux, `"lo0"` on macOS | The Ethernet interface with `192.168.123.xxx` for Unitree G1 | `base_sim.py`, `state_publisher.py`, and policies pass this to `ChannelFactoryInitialize`. Wrong interface usually appears as no low state or no commands. |

Do not use a real Ethernet interface for sim2sim unless you intentionally want DDS traffic there. Do not use localhost for real hardware.

## Joystick and Input Toggles

| Field | Meaning |
| --- | --- |
| `USE_JOYSTICK` | `0` uses keyboard input through `sshkeyboard`; `1` enables a Unitree wireless-controller simulation/subscription path through `pygame`. |
| `JOYSTICK_TYPE` | Supported layouts: `"xbox"` and `"switch"` in `UnitreeSdk2Bridge.SetupJoystick`. |
| `JOYSTICK_DEVICE` | Pygame joystick index, usually `0`. |

When `USE_JOYSTICK: 1`, check joystick visibility before policy startup:

```bash
cd sim2real
python utils/test_xbox.py
```

`test_xbox.py` opens pygame windows and is not suitable for headless machines.

## Simulation Timing and Viewer Fields

| Field | Meaning | Default evidence |
| --- | --- | --- |
| `SIMULATE_DT` | MuJoCo step period; must be larger than the runtime of `viewer.sync()` per config comment. | `0.005` |
| `VIEWER_DT` | Viewer sync/update interval. | `0.02` |
| `PRINT_SCENE_INFORMATION` | Intended to print scene metadata; bridge print call is currently commented in `base_sim.py`. | `True` in config, but no effect unless code is uncommented. |
| `ENABLE_ELASTIC_BAND` | Enables support force in MuJoCo and viewer keys `7/8/9`. | `True` |

If MuJoCo display fails, use the troubleshooting reference rather than silently switching to real hardware.

## Gains, Limits, and Command Safety

`JOINT_KP`, `JOINT_KD`, `MOTOR_KP`, `MOTOR_KD`, `motor_pos_lower_limit_list`, `motor_pos_upper_limit_list`, `motor_vel_limit_list`, and `motor_effort_limit_list` directly affect commanded positions, velocity damping, and clipping.

Important implementation facts:

- `BasePolicy.rl_inference()` clips target joint positions to `motor_pos_lower_limit_list` and `motor_pos_upper_limit_list` when those lists are present.
- `CommandSender.send_command()` applies `MOTOR_KP`/`MOTOR_KD` through a runtime `kp_level`; keyboard and joystick debug keys can change `kp_level` while running.
- `BaseSimulator.compute_torques()` clips simulated torques to `MOTOR_EFFORT_LIMIT_LIST`.
- Weak motors from `WeakMotorJointIndex` use a different Unitree motor mode in `CommandSender.InitLowCmd()`.

Do not adjust gains or motor limits on physical hardware unless a qualified operator has an explicit test plan.

## Observation History and Policy Compatibility

The supplied height policy uses history-rich observations:

- `USE_HISTORY`, `USE_HISTORY_LOCO`, `USE_HISTORY_MIMIC` enable the shared `HistoryHandler` path.
- `history_config`, `history_loco_config`, `history_loco_height_config`, and `history_mimic_config` control the number of history frames by observation key.
- `obs_dims`, `obs_loco_dims`, and `obs_mimic_dims` define expected sizes for observation slices.
- `obs_scales` scales angular velocity, velocity commands, base height, DOF position/velocity, action history, reference upper-body position, and phase features.

Changing any of these fields can cause ONNX input-shape mismatch or behavior drift. Keep the config paired with the exported policy checkpoints unless you know the training-time observation schema.

## Locomotion and Mimic Model Fields

The command-line `--loco_model_path` points to one ONNX locomotion model. The command-line `--mimic_model_paths` points to a root directory containing one subdirectory per mimic key in `mimic_models`.

Config maps used by `MotionTrackingDecLocoPolicy.setup_mimic_policies()`:

| Field | Requirement |
| --- | --- |
| `mimic_models` | For each policy name, a relative ONNX filename. The loader constructs `<mimic_model_paths>/<policy_name>/<filename>`. Missing files raise `FileNotFoundError`. |
| `mimic_robot_types` | Each policy name must map to a key in `robot_dofs`. |
| `robot_dofs` | Boolean-like DOF masks used to place lower/upper/full-body mimic actions into the 29-DOF action vector. |
| `start_upper_body_dof_pos` | Each policy name must provide a 17-value upper-body start pose for interpolation. |
| `motion_length_s` | Each policy name must provide a duration; after phase reaches `1.0`, the runtime switches back to locomotion. |
| `loco_upper_body_dof_pos` | Upper-body reference used when returning to locomotion. |
| `GAIT_PERIOD` | Locomotion phase period for sine/cosine clock features. |

`deepmimic_dec_loco.py` raises `NotImplementedError` for `--use_jit`; use the ONNX path unless the code is extended and verified.

## Height Versus Non-Height Policy Scripts

- `rl_policy/deepmimic_dec_loco.py` implements decoupled locomotion + mimic without the explicit `command_base_height` observation in the locomotion branch.
- `rl_policy/deepmimic_dec_loco_height.py` extends it with `base_height_command`, `history_loco_height_config`, and the default `0.78` base height. The README command uses the height variant and the `...stand_height...model_6600.onnx` locomotion checkpoint.

Match the policy script to the checkpoint family; otherwise ONNX input shapes or runtime behavior may not match.

## Mocap and Data-Collection Fields

`--use_mocap` on policy scripts subscribes to `/odometry` and fills mocap-derived fields, but the default README deployment command does not use it. `listener_deltaa.py` always subscribes to `/odometry` for real-data collection and saves mocap pose/velocity alongside Unitree state/command arrays.
