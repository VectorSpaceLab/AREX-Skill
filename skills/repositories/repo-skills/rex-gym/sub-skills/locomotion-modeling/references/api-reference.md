# Locomotion API reference

This reference records the observed public constructors and call signatures for the
Rex-Gym modeling helpers. Import errors usually mean the public package or its NumPy
dependency is absent; the [inspectors](../scripts/inspect_kinematics.py) provide a
bounded diagnostic without requiring a simulator.

## `Kinematics`

```python
from rex_gym.model.kinematics import Kinematics

Kinematics()
Kinematics.solve(orientation, position, frames=None)
```

- `orientation`: length-3 `[roll, pitch, yaw]`, radians.
- `position`: length-3 `[x, y, z]`, metres.
- `frames`: optional 4×3 foot-frame array-like. If omitted, the instance's default
  frame matrix is used. The implementation stores a supplied matrix on the instance;
  use a fresh object or explicitly pass frames when avoiding state carry-over.
- Return: `(fr_angles, fl_angles, rr_angles, rl_angles, t_frames)`. Each angle item
  is a NumPy shape `(3,)` array; `t_frames` is a NumPy matrix/array with shape `(4,3)`.
  The leg order is **front-right, front-left, rear-right, rear-left**.

The default geometric values are metres:

| quantity | value |
|---|---:|
| body length `_l` / `x_dist` | 0.23 |
| body width `_w` | 0.075 |
| hip offset `_hip` | 0.055 |
| upper leg `_leg` | 0.10652 |
| foot link `_foot` | 0.145 |
| foot-frame width `y_dist` | 0.185 |
| default foot height | 0.2 |

The class also exposes `get_Rx`, `get_Ry`, `get_Rz`, `get_Rxyz`, `get_RT`,
`transform`, and `check_domain`. These are implementation helpers: rotation inputs are
radians, homogeneous transforms are 4×4, and `check_domain` maps values outside
`[-1,1]` to `0.99` or `-0.99`.

### Frame convention

The solver's default frame rows are:

```text
FR  [ +x/2, -y_dist/2, -height ]
FL  [ +x/2, +y_dist/2, -height ]
RR  [ -x/2, -y_dist/2, -height ]
RL  [ -x/2, +y_dist/2, -height ]
```

The return order is not the action order used by the task signal functions. To produce
an ordinary 12-joint Rex command, reorder and flatten as:

```python
command = np.concatenate([fl_angles, fr_angles, rl_angles, rr_angles])
```

That produces **FL, FR, RL, RR**, three joints per leg (`shoulder`, `leg`, `foot`).
Do not reorder twice.

## `GaitPlanner`

```python
from rex_gym.model.gait_planner import GaitPlanner

GaitPlanner(mode)
GaitPlanner.loop(v, angle, w_rot, t, direction, frames=None)
```

The source accepts `mode == "walk"` specially; every other value follows the gallop
branch. Therefore validate mode in caller code when silently accepting a typo would be
unsafe. Constructor state includes `step_offset=0.5` and offsets:

```text
walk:   [0.0, 0.5, 0.5, 0.0]
gallop: [0.0, 0.0, 0.8, 0.8]
```

`loop` returns a NumPy array of shape `(4,3)` in the same FR, FL, RR, RL row order as
its input frames. It computes phase from wall-clock time divided by `t`; values of `t`
less than or equal to `0.01` are replaced by `0.01`. If `frames` is omitted, it creates
the default Kinematics frame matrix. `direction` is normally `1.0` or `-1.0` and affects
swing displacement; task code derives it from the sign of the step length.

Units are intentionally mixed by the source API:

- `v` is a dimensionless trajectory scale in the task configuration; its absolute value
  scales the stance and swing templates.
- `angle` is **degrees** and is converted with `deg2rad` inside stance and swing helpers.
- `w_rot` is the signed rotational trajectory scale. Its sign selects the rotational
  circle branch; the circle angle passed into the helper is in degrees.
- `t` is seconds per gait cycle and is timing-sensitive.
- `frames` are metres; `loop` adds trajectory offsets to those rows.

Useful deterministic helpers are `calculate_stance(phi_st, v, angle)`,
`calculate_bezier_swing(phi_sw, v, angle, direction)`, and
`step_trajectory(phi, v, angle, w_rot, center_to_foot, direction)`. `phi` values are
phase fractions; the planner uses stance for `phi <= 0.5` and swing afterward. The
Bezier swing is built from a fixed degree-11 basis and the current implementation uses
the first ten control-point terms.

Because `loop` reads the clock, repeated calls with the same arguments at different
moments need not match. A caller that needs a fixed phase should test a helper with an
explicit phase or use [inspect_gait.py](../scripts/inspect_gait.py).

## `MotorModel`

```python
from rex_gym.model.motor import MotorModel

MotorModel(motors_num, torque_control_enabled=False, kp=1.2, kd=0)
MotorModel.convert_to_torque(
    motor_commands, motor_angle, motor_velocity, true_motor_velocity,
    kp=None, kd=None,
)
```

For normal use, each vector has length `motors_num`. The return is
`(actual_torque, observed_torque)`, each array-shaped like the command. In position
mode the command is a desired angle; in torque mode it is PWM-like. Both paths clip the
resulting PWM to `[-1,1]` before conversion.

Position-mode PWM is:

```text
pwm = -kp * (motor_angle - motor_commands) - kd * motor_velocity
```

If `kp` or `kd` is omitted, the model fills a length-`motors_num` vector from its
constructor defaults. Per-call gains override those defaults. Torque mode bypasses the
PD calculation and treats `motor_commands` as PWM directly.

The conversion uses these source constants:

```text
MOTOR_VOLTAGE = 32.0
MOTOR_RESISTANCE = 0.186
MOTOR_TORQUE_CONSTANT = 0.0954
MOTOR_VISCOUS_DAMPING = 0
VOLTAGE_CLIPPING = 50
OBSERVED_TORQUE_LIMIT = 5.7
```

Observed torque is the torque-constant current estimate clipped to ±5.7. Actual torque
uses back-EMF and viscous damping, clips net voltage to ±50, interpolates absolute
current over `[0,10,20,30,40,50,60]` to `[0,1,1.9,2.45,3,3.25,3.5]`, reapplies sign,
and multiplies by `set_strength_ratios(ratios)`. Setters are
`set_motor_gains(kp, kd)`, `set_voltage(voltage)`, and
`set_viscous_damping(viscous_damping)`; getters are `get_voltage()` and the source's
misspelled `get_viscous_dampling()`.

## Constants and task consumption

`mark_constants.MARK_DETAILS` maps `base` to 12 motors and `arm` to 18. Its motor-name
list is already in FL, FR, RL, RR leg groups, followed by six arm names for `arm`.
`rex_constants.INIT_POSES` contains 12-value leg poses. `ARM_POSES['rest']` contains
six values. The environment's action transform appends the arm rest vector when the
incoming action length is not the selected mark's motor count; callers should instead
supply the correct 12- or 18-value width deliberately.

The IK pose and walk/gallop task signals call the solver in FR, FL, RR, RL order and
then flatten FL, FR, RL, RR before handing commands to the environment. Open-loop task
signals build the same command-group order directly. See
[motion-and-control](motion-and-control.md) for complete conversion examples.
