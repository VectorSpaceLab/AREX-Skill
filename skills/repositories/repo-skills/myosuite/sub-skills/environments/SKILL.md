---
name: "environments"
description: "Discover, select, and safely control MyoSuite Gymnasium
  environments on the base CPU backend."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MyoSuite environments

Use this sub-skill when a user needs to install the base package, identify a
registered task, create an environment, run a short reset/step rollout, inspect
its spaces or diagnostics, seed it, or close it cleanly. Start with a named
registered environment rather than guessing a model filename.

## Route the request

- Core import, Gymnasium registration, task IDs, reset/step, spaces, rewards,
  `info`, seeding, lifecycle, or safe no-display inspection: handle here.
- Viewer/window behavior and MuJoCo rendering internals: route to
  `simulation-rendering`.
- Model XML editing, IK, or task-specific kinematic changes: route to
  `model-editing-kinematics`.
- Reference trajectories or playback: route to `reference-motion`.
- JAX/MJX execution: route to `mjx-acceleration`; do not imply that a CPU
  smoke proves MJX or CUDA support.
- Long training commands and learner configuration: route to
  `training-integration`.

See [the API reference](references/api-reference.md) for the full contract,
[the task catalog](references/task-catalog.md) for selection, and
[troubleshooting](references/troubleshooting.md) when setup or assets fail.

## Base prerequisites

The supported base route is Python 3.10–3.13 with the package's normal
runtime dependencies, including Gymnasium below 1.3, MuJoCo 3.6.x, NumPy,
Click, and the package data. The verified inspection combination was Python
3.11, MyoSuite 2.12.2, MuJoCo 3.6.0, and Gymnasium 1.2.3. Install the released
package into an isolated environment, or use the project's documented source
installation with all required model assets initialized. Do not install the
MJX/CUDA extras just to run this core route.

Importing `myosuite` imports the package's Gym compatibility helper and then
registers its task suites. If neither `gymnasium` nor the legacy `gym` package
is importable, import fails before an environment can be made. Prefer
Gymnasium for new code.

## Fast path: named, headless rollout

For a standard CPU check, run the bundled safe smoke script:

```bash
python sub-skills/environments/scripts/environment_smoke.py \
  --env-id myoElbowPose1D6MRandom-v0 --steps 3 --seed 123 --render none
```

The script only creates the requested environment, samples bounded actions,
uses `reset(seed=...)`, performs bounded steps, prints contract summaries, and
always calls `close()`. It does not open a viewer, evaluate policy files,
write videos, fetch assets, or execute arbitrary environment arguments. Add
`--check-determinism` to repeat the short rollout with the same reset and
action-space seeds.

The equivalent minimal Python pattern is:

```python
from myosuite.utils import gym

env = gym.make("myoElbowPose1D6MRandom-v0")
try:
    env.action_space.seed(123)
    observation, info = env.reset(seed=123)
    for _ in range(3):
        observation, reward, terminated, truncated, info = env.step(
            env.action_space.sample()
        )
        if terminated or truncated:
            break
finally:
    env.close()
```

Do not call `mj_render()` in a no-display workflow. `gym.make` normally returns
Gymnasium wrappers; use `env.unwrapped` only when the user explicitly needs
MyoSuite internals such as `get_obs_dict`, `get_reward_dict`, `get_proprioception`,
`get_exteroception`, `horizon`, or `get_env_state`.

## Discover before creating

1. Import `myosuite` so registration side effects have run.
2. Prefer an exact ID from [the task catalog](references/task-catalog.md).
3. Check `gym.spec(task_id)` before `gym.make(task_id)`; an unknown ID is a
   selection error, not an installation fix.
4. Read `spec.max_episode_steps` for the wrapper horizon. Core registrations
   include fixed/random tasks and automatically registered `Sarc` and `Fati`
   variants; hand tasks also have `Reaf` variants.
5. If the name is uncertain, list `myosuite.myosuite_env_suite` or filter
   `gym.envs.registry.keys()` instead of probing arbitrary strings.

A valid registry entry does not prove that every model asset can be loaded.
Only `gym.make` followed by `reset` establishes that the selected model is
usable in the current installation.

## Lifecycle and contracts

- `env = gym.make(id, **kwargs)` creates a wrapped task. Keep construction
  kwargs limited to documented task options; do not pass untrusted strings to
  an evaluator.
- `env.reset(seed=seed)` returns `(observation, info)` under Gymnasium. Seed
  the action space separately with `env.action_space.seed(seed)` when comparing
  random-policy rollouts. A legacy Gym installation may return only an
  observation; follow the installed API rather than unpacking blindly.
- `env.step(action)` returns
  `(observation, reward, terminated, truncated, info)`. Stop on either boolean;
  the wrapper enforces the registered time limit through `truncated`, while a
  task's reward dictionary can produce `terminated`.
- `action` must fit `env.action_space`, normally a float32 `Box`. Sampling from
  `action_space` is safer than hand-building controls. Myo muscle tasks may
  internally map normalized controls before MuJoCo advances.
- `observation` is normally a flat NumPy vector in `observation_space`. Its
  task-specific fields can be inspected through the unwrapped task's
  `obs_dict`; do not assume all tasks expose the same keys or dimension.
- `reward` is the configured dense reward scalar by default. `info` contains
  MyoSuite diagnostics such as `time`, `rwd_dense`, `rwd_sparse`, `solved`,
  `done`, `obs_dict`, `rwd_dict`, `proprio_dict`, `visual_dict`, and `state`.
  Treat nested arrays as owned by the environment and copy them before storing.
- Always call `env.close()` in `finally`, including after failed reset, step, or
  inspection. Avoid creating a viewer merely to inspect spaces.

## Safe inspection

Use `environment_smoke.py --list` for a registry snapshot and
`python -m myosuite.utils.examine_env --help` to inspect the supported CLI
surface. The upstream CLI can run random or supplied policies and supports
`--render none`, but it also supports output/video options and policy loading;
use it only with trusted inputs and bounded episode counts. The bundled smoke
script is preferred for automated checks.

For deeper CPU inspection, after a successful reset/step use only public
methods: `env.unwrapped.get_obs_dict(...)`, `get_reward_dict(...)`,
`get_proprioception()`, `get_exteroception()`, `get_env_infos()`, and
`get_env_state()`. Route image capture or viewer setup away from this skill.

## Verification evidence and limits

The base import and a `myoElbowPose1D6MRandom-v0` reset/step smoke passed in the
private Python 3.11 inspection environment after the repository's five MuJoCo
asset submodules were initialized. The source README/minimal example, package
initializers, environment base, Myo base/task registrations, task catalog,
core environment tests, and `examine_env --help` define the claims in the
linked references. Native candidates for later verification are a single pose
reset/step lifecycle, selected core checks from `test_myo`/`test_envs`, and
`examine_env --help`. Optional MJX/JAX/CUDA and display-backed rendering remain
separate, explicitly unverified routes.
