---
name: simulation-environments
description: "Install and operate the legacy Rex-Gym Gym/PyBullet quadruped
  environments, including task, signal, terrain, asset, control-loop, and
  safe-smoke-test decisions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Rex-Gym simulation environments

Use this skill when a task mentions Rex-Gym, a Rex quadruped simulation, a
PyBullet Gym task, locomotion environments, terrains, action spaces, or the
`rex-gym` CLI's `env`, `terrain`, or `mark` arguments. It covers the packaged
legacy environments and their Gym-facing behavior, not policy training.

## Route before acting

- For inverse-kinematics math, gait trajectories, and motor-model details, use
  [locomotion-modeling](../locomotion-modeling/SKILL.md).
- For PPO graphs, training configuration, checkpoints, or policy playback, use
  [training-policy](../training-policy/SKILL.md).
- Use the [task matrix](references/task-matrix.md) to choose a task and signal,
  the [API reference](references/api-reference.md) for constructor and Gym
  contracts, and [terrain and assets](references/terrain-and-assets.md) before
  selecting a non-plane terrain.
- Run the bundled [headless smoke script](scripts/smoke_environment.py) for a
  bounded environment check. It never trains, downloads, or opens a GUI unless
  `--render` is explicitly supplied.
- Diagnose failures with [troubleshooting](references/troubleshooting.md).

## Install the package

The public package name is `rex_gym` (the Python import root is `rex_gym`):

```bash
python -m pip install rex_gym
```

This is a legacy Python 3.7-era project. Prefer an isolated Python 3.7
runtime when reproducing the pinned stack (`gym` 0.17-era APIs, NumPy 1.17,
and PyBullet 2.8-era behavior). Environment-only imports use Gym, NumPy, and
PyBullet; the PPO CLI surface additionally imports TensorFlow 1.x and
TensorFlow Probability 0.8, so do not install or debug that optional surface
for a simulation smoke unless training or playback is requested.

## Select a task and signal

The CLI names are `poses`, `gallop`, `walk`, `turn`, and `standup`. The source
maps their defaults to `ik`, `ik`, `ik`, `ol`, and `ol`, respectively. Override
with exactly one of `--inverse-kinematics` (`-ik`) or `--open-loop` (`-ol`).
The task-specific action dimensions and bounds are in the
[task matrix](references/task-matrix.md); subclasses replace the base class's
12/18-motor action space with compact signal-feedback actions.

The direct Python class imports are:

```python
from rex_gym.envs.gym.poses_env import RexPosesEnv
from rex_gym.envs.gym.gallop_env import RexReactiveEnv
from rex_gym.envs.gym.walk_env import RexWalkEnv
from rex_gym.envs.gym.turn_env import RexTurnEnv
from rex_gym.envs.gym.standup_env import RexStandupEnv
```

For direct construction, pass an explicit terrain id, including for the
ordinary plane. This is required by the current Rex initialization lookup:

```python
from rex_gym.envs.gym.walk_env import RexWalkEnv

env = RexWalkEnv(
    render=False, terrain_type="plane", terrain_id="plane",
    signal_type="ik", target_position=2.0, backwards=False, mark="base")
try:
    observation = env.reset()
    observation, reward, done, info = env.step([0.0, 0.0])
finally:
    env.close()
```

`RexGymEnv(render=False, terrain_type="plane", terrain_id="plane")` is the
low-level environment. It exposes direct desired-motor-angle control; the
five task classes above add compact pose or gait signal controllers. Do not
reimplement those controllers here; route their math to
[locomotion-modeling](../locomotion-modeling/SKILL.md).

## CLI mapping

The CLI converts `--terrain NAME` into both `terrain_type` and `terrain_id`,
converts `--mark NAME` into `mark`, and converts repeated `--arg KEY VALUE`
pairs into constructor keyword arguments; repeated `--flag KEY BOOL` pairs are
merged into the same argument dictionary for boolean constructor keywords.
Relevant examples:

```bash
rex-gym --help
rex-gym train --env walk --log-dir ./logs --terrain plane --mark base \
  --inverse-kinematics --arg target_position 2
rex-gym train --env turn --log-dir ./logs --terrain hills --mark base \
  --open-loop --arg init_orient 0.5 --arg target_orient 3.0
rex-gym policy --env poses --terrain plane --mark base --inverse-kinematics
```

`--env` accepts the names in the legacy mapper, including a `go` entry, but
this package's Gym environment files/register table do not provide a usable
`RexGoEnv`; use the five tasks above. `train` and `policy` load TensorFlow/PPO
surfaces and may render or run indefinitely; they are not smoke commands.
Follow [training-policy](../training-policy/SKILL.md) for those workflows.

## Operate the legacy Gym loop

The API is the old four-return Gym API, not the newer five-return API:

```python
observation = env.reset()
for _ in range(20):
    action = env.action_space.sample()  # only when its declared Box is valid
    observation, reward, done, info = env.step(action)
    if done:
        break
env.close()
```

Use the action dimensions and task bounds from the matrix, and prefer a
zero/known-safe action for smoke tests. `info` contains an `action` key with
the transformed motor command. `done` can mean a fall, a reached target, or
an out-of-trajectory state, depending on the task. `close()` calls the Rex
termination hook; always use `try/finally` so Bullet objects can be released.

Base observations contain motor angles, velocities, torques, and a base
quaternion: length `3*N + 4` (`40` for `base`, `58` for `arm`). Task
observations are compact: poses, walk, turn, and standup expose roll, pitch,
and their rates (length 4); gallop adds 12 motor angles (length 16 for base).
The exact mark-dependent extensions and live quirks are recorded in
[api-reference](references/api-reference.md).

## GUI and headless decisions

Use `render=False` (or the smoke script default) on servers, CI, and displayless
shells. `render=True` opens a PyBullet GUI during construction and therefore
needs a usable display; it is not a headless renderer. GUI IK modes add sliders
for base position/orientation and, for gait tasks, gait parameters. Poses also
supports direct base/orientation slider control. `render(mode="rgb_array")`
returns an image; the legacy implementation returns an empty array for other
modes. Use GUI only for interactive inspection, not unattended validation.

## Acceptance check

A useful environment check must establish import, construction, reset, action
shape, one or more bounded steps, legacy return structure, `info["action"]`,
and cleanup. Run:

```bash
python scripts/smoke_environment.py --task walk --signal ik --terrain random \
  --mark base --target-position 1.0 --direction forward --steps 2
python scripts/smoke_environment.py --help
```

The helper accepts `--target-position` for `walk`/`gallop` and
`--direction forward|backward|random` for `walk`; it reports the constructor
keywords it used. For walk open loop, use `--signal ol` and the helper's
explicit zero action of shape `(8,)`. If a particular packaged terrain fails
on reset, preserve the reported error and switch to `plane` for a repeatable
CPU smoke rather than retrying indefinitely.

The script emits one JSON object and reports missing dependencies, unsupported
asset/terrain combinations, invalid values, or display errors without hiding
the exception class. See [troubleshooting](references/troubleshooting.md) for
source-backed recovery steps.
