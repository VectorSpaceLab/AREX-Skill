# Locomotion troubleshooting

Use the smallest deterministic inspector first. The scripts do not start PyBullet, sleep,
write files, or depend on a particular current directory:

- [inspect_kinematics.py](../scripts/inspect_kinematics.py)
- [inspect_gait.py](../scripts/inspect_gait.py)
- [inspect_motor.py](../scripts/inspect_motor.py)

Run any script with `--help` to see bounded arguments. If a helper import fails, install
or select the public Rex-Gym runtime that provides `rex_gym` and NumPy; the scripts print
a concise, actionable dependency message rather than a traceback.

## IK returns odd angles or clips

**Symptoms:** an unreachable target still returns numbers, a leg looks folded, or a
solver result changes sharply near a pose boundary.

**Checks:**

1. Confirm orientation is `[roll,pitch,yaw]` in radians and position is `[x,y,z]` in
   metres. Do not pass degrees or a quaternion to `Kinematics.solve`.
2. Confirm frames are shape `(4,3)` and rows are FR, FL, RR, RL. Inspect the default
   frame output before introducing a custom frame.
3. Check finite values and estimate reachability using the link lengths. The geometry
   uses hip `0.055`, leg `0.10652`, and foot `0.145` metres, plus body transforms.
4. Remember that the cosine-law domain is clamped to `0.99` or `-0.99` when it leaves
   `[-1,1]`. A successful return does not mean the requested point was reachable.
5. Use a fresh Kinematics instance for independent trials. A supplied `frames` matrix is
   retained by that object for later calls.

The solver has no joint-limit, collision, balance, or terrain check. Route physical
validity and reward consequences to [simulation environments](../../simulation-environments/SKILL.md).

## Legs appear swapped

The solver return is **FR, FL, RR, RL**. The Rex task signal flattening is **FL, FR, RL,
RR**, three joints each. The safe conversion is:

```python
fr, fl, rr, rl, _ = Kinematics().solve(orientation, position, frames)
command = np.concatenate((fl, fr, rl, rr))
```

Do not interpret the source's internal comment about reset leg IDs as a new solver
convention, and do not reorder a command that is already in named motor-list order. The
mark constant names are FL, FR, RL, RR groups.

## Gait mode or phase is wrong

`GaitPlanner("walk")` selects walk offsets. The source treats every other mode string as
the non-walk/gallop branch rather than raising an error. Validate `mode` yourself and
reject typos if mode selection is part of an experiment.

Walk offsets are `[0,.5,.5,0]`; gallop offsets are `[0,0,.8,.8]`. A cycle has a 0.5
stance/swing split. `loop` derives phase from wall-clock time, so two calls with the same
arguments are not a fixed-phase test. `t <= .01` is replaced by `.01`; it is not a
license to use zero or negative periods. Use `step_trajectory` or
[inspect_gait.py](../scripts/inspect_gait.py) for reproducible phase checks.

The gait `angle` is degrees because the source calls `deg2rad`. IK orientation remains
radians. `direction` should agree with the sign of the step length; it changes swing
placement. Rotational motion also depends on the current center-to-foot vector and the
planner's stateful `_alpha`, so do not compare isolated rotational calls as if they were
stateless.

## Array length or shape errors

Use these widths:

| object | expected shape |
|---|---|
| orientation, position | `(3,)` |
| custom Kinematics frames | `(4,3)` |
| each solver leg result | `(3,)` |
| planner frame output | `(4,3)` |
| base motor command | `(12,)` |
| arm-mark motor command | `(18,)` |
| each MotorModel input | `(motors_num,)` |

Flatten only the four angle triples when making a base command. A six-value arm rest
vector belongs after the 12 leg values. The environment source appends
`ARM_POSES['rest']` when an incoming action length differs from the selected mark count;
that fallback does not validate arbitrary malformed lengths, so preflight dimensions in
the caller instead.

## Torque seems capped or gains seem ineffective

There are several different limits:

- Position-mode PD first computes a PWM-like value from target angle, observed angle,
  observed velocity, and gains, then clips PWM to `[-1,1]`.
- Torque mode treats the command as PWM directly and applies the same clip.
- Observed torque is clipped to ±5.7 by the motor helper.
- Actual torque uses net-voltage clipping at ±50 and a finite empirical current/torque
  table, then strength ratios.

Therefore increasing `kp` may stop changing torque once PWM is clipped; it does not raise
the observed-torque limit. `kd` uses observed velocity in the PD term, while true motor
velocity affects back-EMF and viscous damping. `set_strength_ratios` scales actual torque,
not the command and not the observed sensor estimate. Check `actual` and `observed`
separately with [inspect_motor.py](../scripts/inspect_motor.py).

## Overheat protection is missing

`MotorModel` itself does not maintain a thermal timer. In the surrounding Rex class,
optional overheat protection counts time while absolute actual torque exceeds `2.45` and
disables a motor after a source-defined duration of about one second. A standalone motor
probe cannot prove that environment behavior. Check the environment route for reset,
step-time, motor enable state, and safety configuration.

## Model output does not match simulation or reward

This skill covers deterministic transforms and motor-model arithmetic only. It does not
open a Bullet client, load a model, select terrain, compute contacts, calculate rewards,
terminate episodes, or assess falls. A visually bad gait can be caused by timing,
friction, target pose, action normalization, motor direction, or environment setup even
when IK output is numerically valid. Route those questions to
[simulation environments](../../simulation-environments/SKILL.md). Route policy-action
scale, PPO training, and learned correction to [training policy](../../training-policy/SKILL.md).

## Dependency and runtime failures

- **`ModuleNotFoundError: rex_gym`:** the public package is not available to the selected
  interpreter. Run the inspector's help first, then repair the runtime installation; do
  not add an implicit checkout path to a script.
- **NumPy import or array errors:** use a compatible NumPy installation and rerun with
  small finite arrays. The model uses `numpy.matrix` in a few return paths, so convert
  with `np.asarray` before shape comparisons.
- **PyBullet errors during a task:** modeling inspectors deliberately avoid PyBullet.
  Move to the environment route and verify simulator setup there.
- **Non-reproducible gait smoke test:** do not use a wall-clock `loop` call as a golden
  value. Compare fixed `phi` diagnostics, output shape, row order, bounded displacement,
  and expected walk/gallop offsets.
