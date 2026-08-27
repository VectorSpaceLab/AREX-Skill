# Joystick And Observation Contract

## Logitech F710 Map

The documented controller is a Logitech F710. `play.py` opens pygame joystick
index 0 and polls three axes every 100 ms:

```text
x velocity   = -axis 1
lateral vel. = -axis 0
yaw velocity = -axis 3
```

The README describes holding button 4 while moving those axes:

| Documented gesture | Raw axis direction | Command after negation |
|---|---:|---:|
| button 4 + axis 1 negative | stick forward | positive x: move forward |
| button 4 + axis 1 positive | stick backward | negative x: move backward |
| button 4 + axis 0 negative | stick left | positive y: strafe left |
| button 4 + axis 0 positive | stick right | negative y: strafe right |
| button 4 + axis 3 negative | yaw stick left | positive yaw: counterclockwise |
| button 4 + axis 3 positive | yaw stick right | negative yaw: clockwise |

### Important implementation discrepancy

Current `play.py` never calls `get_button(4)`. It applies axis values
unconditionally whenever joystick 0 opens. Therefore button 4 is documented
operator intent, **not an implemented dead-man gate**. Do not claim otherwise.
Keep sticks centered before launch and do not rely on releasing button 4 to
stop motion.

There is also no deadzone, debounce, scaling by the trained command ranges, or
clipping. Raw axis extrema produce commands in `[-1, 1]`. The configured
training ranges are x `[-0.4, 1.2]` m/s, y `[-0.4, 0.4]` m/s, and yaw
`[-0.6, 0.6]` rad/s, so full lateral/yaw stick can exceed the configured
training envelope. Begin with small deflections.

The policy action is computed before the loop writes the latest joystick
commands into `env.commands`. The resulting observation is produced by the
subsequent environment step, so controller changes influence policy input on a
later loop iteration rather than the already-computed action. The first action
uses the environment's initialized observation.

## Safe Controller Check

Before launching Isaac Gym:

1. Put the F710 in the intended hardware mode, connect its receiver, and center
   all sticks.
2. Confirm the operating system exposes the desired controller. On Linux,
   inspect `/dev/input/js*` and access permissions.
3. Run the bundled preflight with `--require-joystick`; it checks device nodes
   only and never initializes pygame.
4. In a separate, non-simulator diagnostic if needed, inspect pygame's reported
   joystick index, axis count, axis values, and button values. Axis numbering
   can differ by OS, driver, and F710 mode. Do not modify robot commands until
   indices 0, 1, and 3 have been confirmed.
5. Launch one environment. Verify near-zero command state before gradual axis
   movement.

If opening joystick 0 fails, playback catches the exception, prints a controller
open failure, starts no polling thread, and continues with all three command
globals at zero. This is acceptable only for a stand/viewer check, not for a
joystick acceptance test.

## X1 Actor Observation

The actor does not accept one instantaneous vector. Its input is a 66-frame
history. Each frame has 47 values in this exact order:

| Slice | Width | Content | Scale/meaning |
|---|---:|---|---|
| `0:2` | 2 | gait phase sine, cosine | `sin(2π phase)`, `cos(2π phase)` |
| `2:5` | 3 | x, y, yaw commands | scaled by `[2, 2, 1]` |
| `5:17` | 12 | joint position offsets | lagged position minus default, scale 1 |
| `17:29` | 12 | joint velocities | lagged velocity, scale 0.05 |
| `29:41` | 12 | previous actions | raw prior policy action |
| `41:44` | 3 | base angular velocity | scale 1 |
| `44:47` | 3 | base Euler roll/pitch/yaw | scale 1 |

The resulting policy tensor is:

```text
[num_envs, 66 * 47] = [num_envs, 3102]
```

The actor extracts the last 5 frames (`235` values) for its short-history state
estimator and reshapes all 3102 values as `[batch, 66, 47]` for the long-history
CNN. It concatenates short history, a 3-value estimated velocity, and a
64-value compressed long history before the actor MLP emits 12 actions.
Supplying only 47 or 235 values is incompatible with the trained policy.

History buffers are initialized with zeros. On reset, all 66 actor-history
slots for reset environments are zeroed; subsequent observations enter one at
a time. This cold-start behavior is part of the training/playback contract.
Do not manually tile the newest observation or bypass environment-managed
history merely to satisfy shape checks.

Playback sets observation noise off, but configured DOF/action lag mechanisms
and their buffers still belong to the environment contract. Do not reconstruct
policy observations from joystick values alone.

## Actions And Joint Order

The policy emits 12 actions for the X1 lower-body joints in asset/config order:

1. left hip pitch
2. left hip roll
3. left hip yaw
4. left knee pitch
5. left ankle pitch
6. left ankle roll
7. right hip pitch
8. right hip roll
9. right hip yaw
10. right knee pitch
11. right ankle pitch
12. right ankle roll

The environment clips policy actions to its broad configured action clip, then
uses position control. The nominal target contribution is:

```text
target joint offset = 0.5 * action
target position     = default joint position + target joint offset
```

Action lag and torque clipping are applied later by the environment. The
12-value actor output, checkpoint architecture, asset DOF order, and
observation history must agree. Shape-compatible but differently ordered
policies are unsafe and should be rejected.

## Command Versus Action

Joystick axes set only the first three velocity commands. They do not directly
set joint targets. The environment combines gait phase and commands into each
47-value observation frame; the trained policy then produces joint actions.
At command norm at or below `0.05`, the configured stand switch treats the
robot as standing and zeros gait phase progression for that environment.
