# Motion and control recipes

Use these recipes to keep geometric frames, task signals, and motor commands aligned.
They intentionally stop before PyBullet reset/step/reward work; route that work to
[simulation environments](../../simulation-environments/SKILL.md).

## 1. Solve a static pose

Start with a fresh `Kinematics` object and explicit units. Orientation is roll, pitch,
yaw in radians; position and frames are metres.

```python
import numpy as np
from rex_gym.model.kinematics import Kinematics

orientation = np.array([0.0, 0.0, 0.0])
position = np.array([0.0, 0.0, 0.0])
ik = Kinematics()
fr, fl, rr, rl, world_frames = ik.solve(orientation, position)

# Solver return: FR, FL, RR, RL. Environment command: FL, FR, RL, RR.
motor_targets = np.concatenate((fl, fr, rl, rr))
assert motor_targets.shape == (12,)
assert np.asarray(world_frames).shape == (4, 3)
```

The zero pose's four leg results are equal in the default symmetric frame, but do not
use equality as a general test: base roll/pitch/yaw, translation, and custom frames make
legs differ. Keep the returned frame matrix if a later gait or inspection needs the
transformed feet.

## 2. Supply custom frames

A gait planner returns a 4×3 frame matrix, and the same ordering must be preserved when
passing it to IK:

```python
frames = np.array([
    [ 0.115, -0.0925, -0.20],  # FR
    [ 0.115,  0.0925, -0.20],  # FL
    [-0.115, -0.0925, -0.20],  # RR
    [-0.115,  0.0925, -0.20],  # RL
])
fr, fl, rr, rl, transformed = Kinematics().solve(
    np.zeros(3), np.zeros(3), frames=frames)
```

The implementation does not provide a joint-limit or collision validator. Before using
custom frames, check the shape, finite values, expected metres, and reachability in the
caller. A target outside the two-link workspace is domain-clamped internally; treat the
result as a diagnostic fallback, not as a physically valid pose.

## 3. Generate walk or gallop frames

```python
import numpy as np
from rex_gym.model.gait_planner import GaitPlanner
from rex_gym.model.kinematics import Kinematics

mode = "walk"                 # "gallop" selects the other source offset pattern
step_length = 0.6
step_angle_deg = 0.0           # angle is degrees, unlike IK orientation
step_rotation = 0.0
period_s = 0.65
forward = 1.0
planner = GaitPlanner(mode)
frames = planner.loop(step_length, step_angle_deg, step_rotation,
                      period_s, forward)
assert np.asarray(frames).shape == (4, 3)
fr, fl, rr, rl, _ = Kinematics().solve(
    np.zeros(3), np.zeros(3), frames=frames)
motor_targets = np.concatenate((fl, fr, rl, rr))
```

Walk uses phase offsets `[0, .5, .5, 0]`; gallop uses `[0, 0, .8, .8]`. Both use a
0.5 stance/swing split. `loop` measures elapsed wall-clock time, so the same arguments
will produce different phases on different calls. `period_s` is clamped to at least
0.01 seconds by the source, but use a meaningful positive period to avoid an unstable,
fast trajectory. The planner's `angle` is passed through `np.deg2rad`; do not pass an
IK yaw in its place.

For backward walking, task code uses a negative step and `direction=-1.0`; preserve the
sign when selecting the direction. Rotational gait adds a circle trajectory from
`w_rot` and the current foot center. Combining large translation and rotation can place
frames outside IK reach, so inspect both frames and solver outputs.

## 4. Reproduce a fixed phase without waiting

For a diagnostic or unit test, use the phase-level helper instead of pretending that a
single `loop` call represents a particular phase:

```python
import numpy as np
from rex_gym.model.gait_planner import GaitPlanner

planner = GaitPlanner("walk")
center = np.array([0.115, -0.0925, -0.2])
coord = planner.step_trajectory(
    phi=0.75, v=0.6, angle=0.0, w_rot=0.0,
    center_to_foot=center, direction=1.0)
assert coord.shape == (3,)
```

`phi <= 0.5` is stance; later phase is Bezier swing. The bundled
[inspect_gait.py](../scripts/inspect_gait.py) evaluates fixed, bounded phases and emits
JSON, making it suitable for smoke tests from any current directory.

## 5. Convert desired positions or PWM to torque

Position-controlled accurate motor model:

```python
import numpy as np
from rex_gym.model.motor import MotorModel

n = 12
model = MotorModel(n, torque_control_enabled=False, kp=1.2, kd=0.0)
target = np.zeros(n)
angle = np.zeros(n)
observed_velocity = np.zeros(n)
true_velocity = np.zeros(n)
actual, observed = model.convert_to_torque(
    target, angle, observed_velocity, true_velocity)
```

The PD error is `target - motor_angle` after the source's negative-error form, and the
velocity term uses the observed velocity. Back-EMF and viscous damping use
`true_motor_velocity`. This distinction matters when latency or noisy observations are
modeled by the surrounding Rex class.

Torque/PWM-controlled model:

```python
n = 3
model = MotorModel(n, torque_control_enabled=True)
pwm = np.array([0.25, 0.0, -0.25])
actual, observed = model.convert_to_torque(
    pwm, np.zeros(n), np.zeros(n), np.zeros(n))
```

Commands beyond `[-1,1]` are clipped before either calculation. This is a PWM clip, not
a joint-angle clip. Actual torque is empirically saturated by the current table and
strength ratios; observed torque is a separate clipped sensor estimate. Use
`set_strength_ratios` with one ratio per motor and values in `[0,1]` as documented by the
source.

## 6. Add the arm safely

```python
import numpy as np
from rex_gym.model import mark_constants, rex_constants

assert mark_constants.MARK_DETAILS["motors_num"]["base"] == 12
assert mark_constants.MARK_DETAILS["motors_num"]["arm"] == 18
arm_rest = rex_constants.ARM_POSES["rest"]
base_command = np.zeros(12)
arm_command = np.concatenate((base_command, arm_rest))
assert arm_command.shape == (18,)
```

The six arm joints are held at the rest extension when a task supplies only the leg
signal for an arm-mark model. Use the selected mark's expected width explicitly; do not
rely on accidental concatenation for malformed actions. The named base motor list is
FL/FR/RL/RR, each `[shoulder, leg, foot]`, followed by arm names for the arm mark.

## 7. Understand task signal consumption

Pose, walk IK, and gallop IK tasks follow this pattern:

```text
base pose + optional gait frames
        ↓
Kinematics.solve → FR, FL, RR, RL angle triples
        ↓
flatten       → FL, FR, RL, RR 12-value motor target
        ↓
Rex environment action transform
        ↓
position targets or accurate MotorModel torque
```

Walk/gallop action dimensions control task-level gait feedback, not direct joint angles:
walk IK and gallop IK use two feedback values; walk open-loop uses eight and gallop
open-loop uses four. Their exact bounds, target stopping, rewards, and episode lifecycle
belong to the environment route. PPO policy construction and action normalization belong
to [training policy](../../training-policy/SKILL.md), not this modeling skill.

## 8. Preflight checklist

Before applying a result, verify:

- orientation is three finite radians and position is three finite metres;
- frames are finite shape `(4,3)` in FR/FL/RR/RL order;
- solver return is reordered exactly once to FL/FR/RL/RR;
- each leg has three values and total width is 12, or 18 with six arm values;
- gait angle is degrees, period is positive seconds, and direction matches travel sign;
- motor vectors all have the selected motor count;
- gains and PWM are not confused with angle or torque units;
- task reward, contact, terrain, and overheating claims are checked in the sibling
  environment documentation rather than inferred from geometric output.
