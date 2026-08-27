# Actions and actuators

## Action config families

Action terms consume the policy tensor and write targets into entities.

| Action config | Use when |
|---|---|
| `JointPositionActionCfg` | Policy outputs target joint positions, usually around the default pose. |
| `RelativeJointPositionActionCfg` | Policy outputs joint deltas relative to current joint positions. |
| `JointVelocityActionCfg` | Policy outputs joint velocity targets. |
| `JointEffortActionCfg` | Policy outputs effort/torque targets. |
| `TendonLengthActionCfg`, `TendonVelocityActionCfg`, `TendonEffortActionCfg` | Policy controls tendons rather than joints. |
| `SiteEffortActionCfg` | Policy applies site-level efforts. |
| `DifferentialIKActionCfg` | Policy controls an end-effector body/site/geom pose delta that is solved into joint updates. |

Common fields:

- `entity_name`: scene entity key.
- `actuator_names`: regex/list matched against actuators or targets.
- `scale`: scalar or mapping from names to per-target scale.
- `offset`: scalar or mapping for normalized policy output.
- `clip`: mapping of output ranges before writing commands.
- `preserve_order`: set when action dimension order must match a model or
  controller contract.

## Actuator config families

Actuator configs live on `EntityArticulationInfoCfg` and define how entity
joints/tendons/sites are controlled.

| Actuator config | Main behavior |
|---|---|
| `XmlActuatorCfg` | Reuse actuators already declared in MJCF. |
| `BuiltinPositionActuatorCfg` | Add MuJoCo implicit position actuator. |
| `BuiltinPdActuatorCfg` | Add MuJoCo implicit PD actuator. |
| `BuiltinMotorActuatorCfg` | Add MuJoCo motor actuator. |
| `BuiltinVelocityActuatorCfg` | Add MuJoCo velocity actuator. |
| `BuiltinDcMotorActuatorCfg` | Add an implicit DC motor model with electrical/thermal options. |
| `IdealPdActuatorCfg` | Explicit PD control in mjlab. |
| `DcMotorActuatorCfg` | Explicit DC motor torque limiting. |
| `LearnedMlpActuatorCfg` | Load a TorchScript MLP actuator model for learned dynamics. |

## Choosing implicit vs explicit actuators

Prefer MuJoCo built-in actuators when their control law matches the need; the
solver can account for damping and velocity-dependent effects more stably.
Use explicit actuators when the control law or learned dynamics are not
representable as MuJoCo actuators.

## Delay modeling

Most actuator configs support delay fields such as min/max lag, hold
probability, update period, and per-environment phase. Use these to model
communication latency without adding custom buffers.

## Differential IK

`DifferentialIKActionCfg` is useful for manipulation tasks where the policy
outputs Cartesian deltas. Key choices:

- `frame_type`: `body`, `site`, or `geom`.
- `frame_name`: target frame name.
- `use_relative_mode`: whether actions are relative deltas.
- `delta_pos_scale` and `delta_ori_scale`: scale policy outputs.
- `damping`, `max_dq`, `position_weight`, `orientation_weight`: solver tuning.
- `joint_limit_weight`, `posture_weight`, `posture_target`: bias away from bad
  configurations.

Start with small scales and a tiny environment count. Debug target frame names
before tuning solver weights.
