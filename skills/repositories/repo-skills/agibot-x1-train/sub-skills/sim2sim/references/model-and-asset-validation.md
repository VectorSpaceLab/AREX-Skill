# Model and asset validation

## X1 policy contract

The `x1_dh_stand` config fixes the deployment dimensions:

| Quantity | Contract | Derivation/source role |
|---|---:|---|
| actions | 12 | six joints per leg |
| one observation | 47 | 5 + 12 + 12 + 12 + 3 + 3 |
| long-history frames | 66 | policy long-history input channels |
| policy input | 3102 | `66 * 47` |
| short-history frames | 5 | state-estimator input history |
| estimator input | 235 | `5 * 47` |
| raw command fields | 4 | `vx`, `vy`, `yaw`, heading; heading is disabled |
| effective command observation | 3 | `vx`, `vy`, `yaw`, plus phase sin/cos |
| MuJoCo qpos | 19 | 7 free-base values + 12 actuated joint values |
| MuJoCo qvel | 18 | 6 free-base velocities + 12 joint velocities |

The 47-value deployment frame is assembled in this order:

```text
0..4      sin(phase), cos(phase), scaled x velocity, scaled y velocity, scaled yaw velocity
5..16     q[-12:] - default_dof_pos, scaled by dof_pos=1
17..28    dq[-12:], scaled by dof_vel=0.05
29..40    previous 12-action vector
41..43    body angular velocity, scaled by ang_vel=1
44..46    quaternion converted to Euler XYZ, scaled by quat=1
```

The stand flag is **not** part of this deployment contract: the config has
`num_single_obs=47` and `add_stand_bool` remains false. If a policy was
trained/exported with a 48-value frame, it is a different artifact and must not
be fed to this route.

The exporter wraps three learned components. It takes the last 235 entries as
short history, reshapes the complete input to `[batch, 66, 47]` for the long
history module, estimates three values from the short history, concatenates
short history + estimator output + compressed long history, and calls the actor.
The output is the actor mean, with shape `[batch, 12]`. The JIT file is normally
`policy_dh.jit`; it is not a raw actor-only file and not a runner checkpoint.
Validate this interface with an explicitly allowed TorchScript test, not by
executing the interactive sim2sim source.

## Joint and actuator order

The source config's default-angle insertion order and the MJCF actuator order
are the same 12-leg sequence:

```text
left_hip_pitch
left_hip_roll
left_hip_yaw
left_knee_pitch
left_ankle_pitch
left_ankle_roll
right_hip_pitch
right_hip_roll
right_hip_yaw
right_knee_pitch
right_ankle_pitch
right_ankle_roll
```

The URDF names these revolute joints with a `_joint` suffix. The URDF is the
Isaac Gym asset contract; the MJCF is the sim2sim asset contract. Do not sort
joint names alphabetically or infer the order from actuator display names.

The config's default target positions, in the sequence above, are:

```text
[ 0.40,  0.05, -0.31, 0.49, -0.21, 0.00,
 -0.40, -0.05,  0.31, 0.49, -0.21, 0.00 ] rad
```

The sim2sim script initializes the last 12 qpos entries from these values and
computes position PD as:

```text
(target_action + default_dof_pos - q) * kp - dq * kd
```

with target action equal to `0.5 * policy_action`. The repeated six-joint gain
vectors are:

```text
kp = [30, 40, 35, 100, 35, 35] * 2
kd = [3, 3, 4, 10, 0.5, 0.5] * 2
```

The source clamps the resulting torque against a nominal 500-value limit for
each joint before assigning `data.ctrl`; the MJCF motors also declare
per-actuator control ranges. Preserve both model and controller contracts when
comparing behavior.

## MJCF include graph

The top-level `xyber_x1_flat.xml` is intentionally small:

```xml
<include file="robot/xyber_x1/xyber_x1_serial.xml" />
<include file="environment/flat.xml" />
```

The robot include defines the X1 body tree, the free joint, 12 hinges, motors,
IMU/velocity sensors, the home keyframe, and a compiler with `angle='radian'`,
`eulerseq="XYZ"`, `autolimits="true"`, and `meshdir="../meshes"`. Resolve
that mesh directory relative to the top-level X1 MJCF model as MuJoCo expands
the include graph; it must reach the sibling X1 `meshes/` directory. The
environment include supplies the flat plane, lighting, textures, and visual
settings.

The source asset should compile to these useful structural checks:

```text
nq=19, nv=18, nu=12, nbody=31, nsensor=29, timestep=0.001
```

These counts are a fixture for the supplied X1 asset, not a general requirement
for every future robot. A count mismatch usually means an include, mesh, model
revision, or wrong task was selected.

The robot includes 29 sensors: five body-level sensors (orientation, angular
velocity, position, velocity, acceleration), 12 joint-position sensors, and 12
joint-velocity sensors. The native observation code specifically consumes the
orientation and body-angular-velocity sensors and reads qpos/qvel directly.

The bundled preflight parses each include without evaluating arbitrary code,
checks include traversal stays under the declared asset root, resolves every
MJCF `<mesh file=...>` under the compiler mesh directory, checks actuator and
hinge order, checks required sensor names, and validates the 19-value home
keyframe. It also parses `urdf/x1.urdf`, checks the 12 revolute joints and every
URDF mesh reference relative to the URDF's `../meshes/` compiler directory.

## MuJoCo state conversion facts

The native script extracts:

- `q = data.qpos`, `dq = data.qvel`, then keeps the final 12 entries for the
  actuated joints;
- body orientation sensor data in MuJoCo `[w,x,y,z]` layout, reordered to
  SciPy `[x,y,z,w]` before applying inverse rotations;
- base-frame linear velocity by applying the inverse body rotation to
  `data.qvel[:3]`;
- body angular velocity from `body-angular-velocity`;
- gravity in the base frame by inverse-rotating `[0,0,-1]`;
- Euler angles from the reordered quaternion, normalized into approximately
  `[-pi, pi]`.

The training environment uses the same broad deployment features but the
native sim2sim reconstruction is not a proof of exact sensor parity. The
script also has two source-level conditional bugs:

```python
if '5_link' or 'ankle_roll' in body_name:
if 'base_link' or 'waist_link' in body_name:
```

The first condition is always truthy and appends every body as a foot
candidate; the second is always truthy and overwrites `base_pos` while
iterating. In this source revision that can make foot/base logging misleading.
Do not silently claim that logger diagnostics prove the sensor extraction is
correct; use the model's named bodies/sites and an explicit source fix in a
separately recorded revision if diagnostic fidelity matters.

## Timing and comparison checks

The X1 config gives `sim.dt=0.001` and `control.decimation=10`; sim2sim repeats
these in its local config and updates policy observations when
`count_lowlevel % decimation == 0`. At a policy update it inserts the current
previous-action vector before calling the policy, then holds the resulting
position target for the next low-level steps. Compare runs only after checking:

1. the MuJoCo timestep is 0.001, not the viewer's wall-clock rate;
2. policy updates are every 10 physics steps, not every rendered frame in a
   modified loop;
3. the action vector has not been shifted by one frame;
4. default angles, gain order, action scale, observation scales, and clipping
   match the config;
5. the flat plane and gravity/up axis agree with the expected X1 model.

A zero-command stand check is useful for XML/controller sanity but does not
measure locomotion quality. Record whether a run used keyboard/joystick
commands, zero commands, or a replayed command trace.
