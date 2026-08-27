# Rex-Gym API reference

This reference records the constructor signatures and runtime facts of the
legacy package's environment classes. It follows the source classes and a
live import/reset/step probe under the package's Python 3.7-era dependency
set.

## Imports and registration

Use direct imports when you need a class and explicit arguments:

```python
from rex_gym.envs.rex_gym_env import RexGymEnv
from rex_gym.envs.gym.poses_env import RexPosesEnv
from rex_gym.envs.gym.gallop_env import RexReactiveEnv
from rex_gym.envs.gym.walk_env import RexWalkEnv
from rex_gym.envs.gym.turn_env import RexTurnEnv
from rex_gym.envs.gym.standup_env import RexStandupEnv
```

Gym registration is performed when `rex_gym.playground` is imported. The
registered ids and class entry points are:

| Gym id | Class | Module |
|---|---|---|
| `RexGalloping-v0` | `RexReactiveEnv` | `rex_gym.envs.gym.gallop_env` |
| `RexWalk-v0` | `RexWalkEnv` | `rex_gym.envs.gym.walk_env` |
| `RexTurn-v0` | `RexTurnEnv` | `rex_gym.envs.gym.turn_env` |
| `RexStandup-v0` | `RexStandupEnv` | `rex_gym.envs.gym.standup_env` |
| `RexPoses-v0` | `RexPosesEnv` | `rex_gym.envs.gym.poses_env` |

A Gym factory call should still supply `render=False` and
`terrain_id="plane"` for a safe direct check:

```python
import gym
import rex_gym.playground

env = gym.make("RexWalk-v0", render=False,
               terrain_type="plane", terrain_id="plane")
try:
    observation = env.reset()
finally:
    env.close()
```

## Common lifecycle and low-level class

`RexGymEnv` accepts the broad simulation controls (`render`, `mark`,
`terrain_type`, `terrain_id`, `target_position`, `target_orient`,
`init_orient`, `backwards`, timing, motor, latency, and reward options). Its
constructor creates Bullet, loads a plane and Rex, resets once, then builds
spaces. Its direct defaults include `render=True`, `signal_type="ik"`,
`terrain_type="plane"`, `terrain_id=None`, and `mark="base"`; override render
and terrain id in non-interactive code.

The base action is a desired motor-angle vector and has length `N`, with a
nominal Box range `[-1, 1]` per component. `N=12` for `mark="base"` and
`N=18` for `mark="arm"`. If a base-level action length differs from the mark's
motor count, `_transform_action_to_motor_command` appends the arm rest pose;
task classes use this to turn a 12-motor signal into an 18-motor arm command.

The base observation is the concatenation of:

1. `N` motor angles;
2. `N` motor velocities;
3. `N` motor torques;
4. four base-orientation quaternion components.

Thus the base observation has length `3*N+4`: 40 for base, 58 for arm. The
base `step(action)` returns `(observation, reward, done, info)`, where
`info == {"action": transformed_motor_command}` in the current implementation.
There is no `terminated`/`truncated` split.

Useful accessors after reset/step are `get_rex_motor_angles()`,
`get_rex_motor_velocities()`, `get_rex_motor_torques()`,
`get_rex_base_orientation()`, `get_objectives()`, `is_fallen()`,
`objective_weights`, `pybullet_client`, `ground_id`, and `env_step_counter`.
`set_time_step(control_step, simulation_step=0.001)` rejects a control step
smaller than the simulation step.

## Task-specific constructor keywords

| Class | Task keywords | Reset/termination behavior |
|---|---|---|
| `RexPosesEnv` | `base_y`, `base_z`, `base_roll`, `base_pitch`, `base_yaw`, `signal_type="ik"` | Cycles pose targets when no base target is supplied; reward is 1 while running and its `is_fallen()` override never terminates. |
| `RexReactiveEnv` | `target_position`, `signal_type="ik"` or `"ol"` | Random target in roughly 1–3 when target is absent; target braking, fall, or lateral out-of-trajectory can end an episode. |
| `RexWalkEnv` | `target_position`, `backwards`, `signal_type="ik"` or `"ol"` | Random forward/backward direction when `backwards` is absent; target and fall/out-of-trajectory checks can end an episode. |
| `RexTurnEnv` | `init_orient`, `target_orient`, `signal_type="ik"` or `"ol"` | Random start/target orientations when absent; target orientation is followed by a delay before `done`. |
| `RexStandupEnv` | `signal_type="ol"` (constructor accepts the keyword) | Starts from `rest_position`, drives toward `stand`, and terminates on the class's roll/pitch fall test. |

Angles are radians. `target_position` is along the x-direction; the task code
uses absolute values in target checks/reward paths. `backwards=False` is the
explicit choice for forward walk; `None` lets `RexWalkEnv.reset()` choose.

## Observation and action facts

| Task | Default signal | Observation (base mark) | Action shape and declared range |
|---|---|---:|---|
| poses | IK | `(4,)`: roll, pitch, roll rate, pitch rate | `(1,)`, `[-0.1, 0.1]` |
| gallop | IK | `(16,)`: four base values + 12 motor angles | IK `(2,)`, intended `[-0.4, 0.4]`; OL `(4,)`, intended `[-0.3, 0.3]` |
| walk | IK | `(4,)`: four base values | IK `(2,)`, `[-0.4, 0.4]`; OL `(8,)`, `[-0.01, 0.01]` |
| turn | OL | `(4,)`: four base values | IK or OL `(2,)`, `[-0.01, 0.01]` |
| standup | OL | `(4,)`: four base values | `(1,)`, `[-0.1, 0.1]` |

The gallop implementation constructs its `spaces.Box` with the positive
maximum as `low` and the negative maximum as `high`; a live Gym 0.17 probe
therefore exposes reversed bounds for both gallop signals. The environment's
`step` path uses the vector length and does not independently reject an
out-of-Bounds value. Treat this as a compatibility defect: do not use
`action_space.sample()` for gallop smoke; use a bounded zero or a controller
output and record the declared bounds.

With `mark="arm"`, motor-bearing observations and transformed `info["action"]`
can grow to 18 motors, but compact task observations remain task-defined.
The arm URDF and six arm rest motors are packaged with the environment.
