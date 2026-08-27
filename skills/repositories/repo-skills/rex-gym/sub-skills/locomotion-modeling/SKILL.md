---
name: locomotion-modeling
description: "Use Rex-Gym's deterministic kinematics, Bezier gait, constants,
  and motor model helpers to turn poses or gait parameters into correctly
  ordered leg commands and bounded torques."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Rex locomotion modeling

Use this sub-skill when a task mentions Rex-Gym inverse kinematics, `Kinematics.solve`,
Bezier trajectories, `GaitPlanner`, leg frames, motor PD/torque, walk or gallop phase,
mark/motor constants, 12-joint versus 18-motor commands, or action-to-motor conversion.
It is a source-backed operating guide, not a simulator lifecycle guide.

## Route first

- For PyBullet connection/reset/step lifecycle, terrain, observations, rewards, falls,
  or task termination, follow [simulation environments](../simulation-environments/SKILL.md).
- For PPO policy architecture, training, checkpoints, and evaluation, follow
  [training policy](../training-policy/SKILL.md).
- Use the bundled [API reference](references/api-reference.md) for signatures and
  constants, [motion and control](references/motion-and-control.md) for recipes, and
  [troubleshooting](references/troubleshooting.md) when a result is surprising.
- Run [inspect_kinematics.py](scripts/inspect_kinematics.py),
  [inspect_gait.py](scripts/inspect_gait.py), or
  [inspect_motor.py](scripts/inspect_motor.py) for bounded diagnostics.

## Model pipeline

1. Choose the mark and command width. The base has 12 leg motors (four legs × three
   joints); the arm mark has 18 motors and appends six arm joints. Constants and names
   are in `rex_constants` and `mark_constants`; do not invent a second ordering.
2. Define base pose as `orientation=[roll, pitch, yaw]` and `position=[x, y, z]`.
   Kinematics uses radians and metres. Define four foot frames as a 4×3 matrix in
   solver order **FR, FL, RR, RL**.
3. For a static pose, call `Kinematics.solve`. For motion, call `GaitPlanner.loop`
   to obtain updated frames, then pass those frames to `solve`.
4. Convert the solver's four 3-angle results to the environment's motor command order
   **FL, FR, RL, RR**, three values per leg. This reorder is required by the task
   signal code even though the solver returns FR, FL, RR, RL.
5. In position control, pass desired joint angles to the environment. In torque control,
   pass one bounded PWM-like value per motor to `MotorModel.convert_to_torque`; inspect
   both returned actual and observed torque before applying simulation controls.

## Verified recipes

Static IK with default frames:

```python
import numpy as np
from rex_gym.model.kinematics import Kinematics

ik = Kinematics()
fr, fl, rr, rl, transformed = ik.solve(
    orientation=np.zeros(3), position=np.zeros(3)
)
command = np.concatenate([fl, fr, rl, rr])  # 12 values: FL, FR, RL, RR
assert command.shape == (12,)
assert np.asarray(transformed).shape == (4, 3)
```

A gait-to-command step:

```python
import numpy as np
from rex_gym.model.gait_planner import GaitPlanner
from rex_gym.model.kinematics import Kinematics

planner = GaitPlanner("walk")
ik = Kinematics()
frames = planner.loop(v=0.6, angle=0.0, w_rot=0.0, t=0.65, direction=1.0)
fr, fl, rr, rl, _ = ik.solve(np.zeros(3), np.zeros(3), frames)
command = np.concatenate([fl, fr, rl, rr])
```

The loop is clock-driven: `t` is the period in seconds and the phase comes from wall
clock time. For reproducible phase diagnostics, use
[inspect_gait.py](scripts/inspect_gait.py), which evaluates bounded fixed phases rather
than sleeping or opening PyBullet.

Torque conversion:

```python
import numpy as np
from rex_gym.model.motor import MotorModel

model = MotorModel(motors_num=12, torque_control_enabled=False, kp=1.2, kd=0.0)
tau_actual, tau_observed = model.convert_to_torque(
    motor_commands=np.zeros(12), motor_angle=np.zeros(12),
    motor_velocity=np.zeros(12), true_motor_velocity=np.zeros(12),
)
```

For position control, `motor_commands` are target angles. For torque control, construct
`MotorModel(12, torque_control_enabled=True)` and supply PWM-like commands in `[-1, 1]`;
the implementation clips them before its DC-motor calculation. All five input arrays
must broadcast to the motor count in normal use.

## Constants and limits that matter

- `Kinematics` uses body dimensions `x_dist=0.23`, `y_dist=0.185`, and default foot
  height `0.2` metres. Its default frames are
  `[[.115,-.0925,-.2],[.115,.0925,-.2],[-.115,-.0925,-.2],[-.115,.0925,-.2]]`.
- `mark_constants.MARK_LIST` is `['base', 'arm']`. `MARK_DETAILS['motors_num']` is
  12 for `base` and 18 for `arm`; the arm's six rest values are
  `[-1.6,-1.6,0,0,1.6,0]`.
- `INIT_POSES` supplies named 12-value poses such as `stand`, `stand_ol`, `gallop`,
  `stand_low`, `stand_high`, and `rest_position`. These values are radians despite
  their source being plain arrays. `ARM_POSES['rest']` is six radians.
- Motor defaults are `kp=1.2`, `kd=0`, voltage `32`, resistance `0.186`, torque
  constant `0.0954`, and zero viscous damping. PWM is clipped to `[-1,1]`; observed
  torque is clipped to ±5.7; net voltage is clipped to ±50 before the empirical
  current/torque interpolation. Strength ratios scale actual torque.

## Scope boundary and limitations

IK clamps the cosine-law domain to ±0.99 (not ±1) when a target is unreachable, so a
returned angle is a bounded fallback rather than proof that the pose is reachable.
The solver is a geometric model: it does not validate joint limits, collisions,
contact, terrain, balance, or rewards. The gait planner is an open-loop trajectory
reference; it does not guarantee foot contact or stable locomotion. The motor helper
models torque/PWM and does not itself simulate PyBullet, thermal shutdown, or policy
learning. Keep task semantics and evaluation in the routed sibling skills.

Read the detailed links above before changing conventions; then run the relevant
self-contained inspector and compare shapes, phase, ordering, and clipping behavior.
