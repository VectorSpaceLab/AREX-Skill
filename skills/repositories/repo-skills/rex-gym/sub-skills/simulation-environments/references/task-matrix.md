# Rex-Gym task matrix

Choose the smallest task that matches the requested behavior. The names and
classes below are the package's environment mapping, not PPO policy ids.

## Task selection

| CLI env | Python class | Goal | Default signal | Observation (base) | Action shape |
|---|---|---|---|---:|---:|
| `poses` | `RexPosesEnv` | Move the body through static base poses while standing | `ik` | 4 | 1 |
| `gallop` | `RexReactiveEnv` | Start/stop a gallop at a target x position | `ik` | 16 | IK 2; OL 4 |
| `walk` | `RexWalkEnv` | Walk to a target x position, forward or backward | `ik` | 4 | IK 2; OL 8 |
| `turn` | `RexTurnEnv` | Turn in place to a target yaw/orientation | `ol` | 4 | IK 2; OL 2 |
| `standup` | `RexStandupEnv` | Rise from `rest_position` to the stand pose | `ol` | 4 | 1 |

All compact observations contain `[roll, pitch, roll_rate, pitch_rate]` in
that order. Gallop then appends the 12 motor angles when using the base mark.
The base low-level environment has a different 3N+4 observation and N-motor
action contract; see [api-reference](api-reference.md).

## Signal choice and action values

| Task | IK feedback | Open-loop feedback | Signal behavior in the source |
|---|---:|---:|---|
| poses | `(1,)`, ±0.1 | not implemented as a pose signal | IK solves a pose from base position/orientation and stages it with one ramp coefficient. |
| gallop | `(2,)`, intended ±0.4 in the class (the README describes ±0.3) | `(4,)`, intended ±0.3 | IK uses a gallop planner and two start/stop feedback values; OL modifies front/rear leg and foot pose offsets. |
| walk | `(2,)`, ±0.4 | `(8,)`, ±0.01 | IK uses gait start/stop values; OL uses sinusoidal leg/foot references and eight per-leg corrections. |
| turn | `(2,)`, ±0.01 | `(2,)`, ±0.01 | IK adjusts step rotation and period; OL alternates turning poses with shoulder/foot corrections. |
| standup | not the documented mode | `(1,)`, ±0.1 | OL applies a timing/brake coefficient before holding the stand pose. |

The gallop Box has a source-level reversed low/high declaration in the legacy
implementation. Use zero or another explicitly chosen vector of the right
length for a smoke; do not infer a valid sampler from its `Box` object. A
requested signal must be exactly `ik` or `ol`; the CLI flags select one, and if
both flags are supplied the parser chooses `ol`.

## Task-specific controls

### Poses

The target is a body pose, not locomotion. In headless mode, supply one of
`base_y`, `base_z`, `base_roll`, `base_pitch`, or `base_yaw`; the environment
chooses a target when all are absent. In GUI IK mode, sliders expose base x/y/z
and roll/pitch/yaw. The constructor has no `base_x` keyword; its internal base x
is fixed near `0.01`.

### Gallop

`target_position` is the x target. If it is absent or false, reset chooses a
random target in approximately `[1, 3]`. The implementation brakes after the
goal and can report `done` for a fall or lateral drift. The README describes
forward and backward gallop experiments, but this class's public constructor
does not expose a `backwards` keyword; do not promise backward gallop through
the current task API.

### Walk

`target_position` is the x target. `backwards=False` makes the forward choice;
`backwards=True` uses a shorter negative step and negative target range;
`backwards=None` randomizes the direction at reset. If no target is given,
reset randomizes one. IK's step length/period defaults differ by direction;
OL uses the source sinusoid with leg amplitude `0.1`, foot amplitude `0.2`,
and period `1/8` seconds, plus eight small feedback corrections.

### Turn

Pass `init_orient` and `target_orient` in radians to make the episode
repeatable. If either is absent/falsy, reset randomizes orientations in roughly
`[0.2, 6]`. A small cube is placed in the target direction as a visual marker.
The environment chooses the shorter turning direction using the angle
 difference and stops after the target check plus a delay.

### Standup

The reset pose is `rex_constants.INIT_POSES['rest_position']`; the target is
`INIT_POSES['stand']`. It is intentionally open-loop in the README and source.
Its reward is based on distance from a base target around z=`0.21`; its
termination override is the roll/pitch fall test rather than a target-goal
flag.

## CLI arguments

The CLI's `--arg` pairs are passed as floats and are not schema-checked before
constructor invocation. Use only keywords accepted by the chosen class:

| CLI argument | Tasks | Meaning |
|---|---|---|
| `target_position` | gallop, walk | x-direction goal |
| `init_orient` | turn | starting yaw in radians |
| `target_orient` | turn | target yaw in radians |
| `base_y`, `base_z`, `base_roll`, `base_pitch`, `base_yaw` | poses (also accepted by low-level base) | static body pose target |
| `step_length`, `step_rotation`, `step_angle`, `step_period` | low-level/gait-compatible constructors | gait planner inputs; route gait semantics to the sibling modeling skill |
| `backwards` | walk direct API | forward/backward selection; CLI boolean flags are a separate parser surface |

The CLI always adds `terrain_type`, `terrain_id`, and `mark` from their named
options. `--log-dir` is required by `train` even when the intent is only to
launch a rendered playground. Avoid `train` and `policy` for environment
inspection; they enter the PPO/TensorFlow surface.
