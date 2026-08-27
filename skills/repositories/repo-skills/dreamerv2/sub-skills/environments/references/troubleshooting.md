# Environment troubleshooting

Diagnose environment construction separately from full DreamerV2 training. A
successful import does not prove assets, rendering, action translation, or GPU
training readiness.

## Establish the era-compatible baseline

The verified package combination is DreamerV2 2.2.0, TensorFlow 2.6.0,
TensorFlow Probability 0.14.1, and Gym 0.23.1. The environment adapters also
use deprecated NumPy aliases such as `np.bool`; a modern NumPy release can fail
while merely reading `obs_space`. Keep the TensorFlow 2.6-era dependency set in
an isolated environment instead of upgrading one library in place.

Record package versions without launching training:

```bash
python - <<'PY'
import importlib
for name in (
    'dreamerv2', 'gym', 'numpy', 'tensorflow',
    'tensorflow_probability', 'PIL', 'cloudpickle'):
  try:
    module = importlib.import_module(name)
    print(name, getattr(module, '__version__', 'installed'))
  except Exception as exc:
    print(name, type(exc).__name__, str(exc))
PY
```

The native module route asserts that TensorFlow sees a GPU. Environment-only
probes below may run without that assertion; passing them does not authorize a
native training run. Use the training sub-skill for the GPU and bounded-run
gates.

## `ModuleNotFoundError: gym`

The base adapter imports legacy `gym` at module import time. Install the
version required by the verified stack:

```bash
python -m pip install 'gym==0.23.1'
```

Do not replace it with Gymnasium and assume compatibility. Gymnasium has
different reset/step, registry, render, and wrapper contracts.

If `PIL` is missing when a custom image has to be resized:

```bash
python -m pip install pillow
```

## Missing Atari modules or ROMs

Symptoms include missing `gym.envs.atari`, missing `atari_py`, an empty game
list, or an error saying a game is not found.

The era adapter needs both Gym's Atari integration and `atari_py`:

```bash
python -m pip install 'gym[atari]==0.23.1' atari_py
python - <<'PY'
import gym.envs.atari
import atari_py
print('Known ROMs:', atari_py.list_games())
PY
```

ROM binaries are not ordinary Python dependencies and carry separate license
terms. Obtain them lawfully, then import the directory into `atari_py`:

```bash
python -m atari_py.import_roms /absolute/path/to/licensed-rom-directory
```

Re-run `atari_py.list_games()` and confirm the requested game token. The
adapter maps `james_bond` to `jamesbond`; other names must match the installed
ROM registry. Do not debug DreamerV2 policy code until direct Atari
construction and reset work.

## Missing `dm_control`, MuJoCo rendering, or key errors

Install a `dm_control`/MuJoCo combination compatible with the pinned Python and
TensorFlow-era environment:

```bash
python -m pip install dm_control
```

Probe physics and rendering independently:

```bash
MUJOCO_GL=egl python - <<'PY'
from dm_control import suite
env = suite.load('walker', 'walk')
step = env.reset()
image = env.physics.render(64, 64, camera_id=0)
print(step.first(), image.shape, image.dtype)
PY
```

Common failures and boundaries:

- `libEGL`, OpenGL, or context errors: ensure the host/container exposes a
  working EGL implementation and compatible display/GPU driver libraries.
  DreamerV2's DMC adapter sets `MUJOCO_GL=egl`; set it before importing other
  MuJoCo bindings during standalone probes as well.
- invalid camera: use `dmc_camera=-1` for the adapter's task defaults or probe a
  valid camera ID for the chosen domain.
- `mjkey.txt`/license error: some old MuJoCo distributions require a valid key
  in the location expected by that distribution. Newer license-free MuJoCo
  installations do not. Follow the installed MuJoCo version's license and key
  instructions; do not copy an unverified key.
- missing manipulator/locomotion task: `manip` and `locom` use different
  `dm_control` loaders from ordinary suite domains. Confirm the exact factory
  exists in the installed release.
- empty proprioceptive key: the adapter intentionally omits DM Control entries
  whose shape is `(0,)`.

A headless rendering failure blocks both `dmc_vision` and the always-present
DMC `image` output, even if the intended model preset uses proprioception.

## Missing Crafter or incompatible task

Install the environment package in the same isolated runtime:

```bash
python -m pip install crafter
python - <<'PY'
import crafter
env = crafter.Env()
print(env.observation_space, env.action_space)
print(type(env.reset()).__name__)
env.close()
PY
```

The native task suffix is exactly `reward` or `noreward`, and native Crafter
requires `action_repeat == 1`. Crafter statistics/video directories need write
permission when a recorder output directory is supplied. Inspect the installed
Crafter observation shape and dtype rather than assuming an incompatible newer
release has the same API.

## Wrong task separator or suite token

Symptoms:

- `ValueError` while unpacking the task: no underscore followed the suite.
- `NotImplementedError(<suite>)`: the first token is not `dmc`, `atari`, or
  `crafter`.
- DMC load error for domain `ball`: `dmc_ball_in_cup_catch` was used instead of
  the adapter's required alias `dmc_cup_catch`.
- Crafter list/index error: task suffix was not `reward` or `noreward`.

Print the two parsed parts before constructing anything:

```bash
TASK=dmc_walker_walk python - <<'PY'
import os
suite, task = os.environ['TASK'].split('_', 1)
print({'suite': suite, 'suite_task': task})
PY
```

For custom Gym environments, do not invent `gym_<id>`; instantiate the Gym
environment in Python and use `dreamerv2.api.train`.

## `too many values to unpack` or reset returns a tuple

DreamerV2's `GymWrapper` expects:

```text
reset() -> observation
step(action) -> observation, reward, done, info
```

A modern environment may instead return `(observation, info)` and a five-item
step result. Prefer an era-compatible environment version. Otherwise use the
`LegacyStepAPI` shim in `custom-gym.md`, making sure `terminated` maps to
`info['is_terminal']` and `terminated or truncated` maps to `done`.

Do not discard the distinction by setting terminal to `done`: replay discounts
would then treat a time-limit truncation as an absorbing terminal state.

## Missing keys, immutable observations, or nonnumeric values

`GymWrapper` augments dict observations in place. Return a fresh mutable `dict`
on every reset and step; a read-only mapping can fail when it adds `reward` and
lifecycle keys.

Remove or encode strings, Python objects, ragged lists, and text mission fields.
Every model/replay entry should have a static numeric shape. Ensure all reset
keys are also present on every step and vice versa. Never let a custom
observation overwrite `reward`, `is_first`, `is_last`, or `is_terminal`.

## Image dtype or shape is wrong

Expected pixel rules:

- channel-last `(H, W, C)`;
- `C` is normally 1 or 3;
- `uint8` values in `[0, 255]`;
- fixed shape across reset and step.

Inspect direct and wrapped outputs:

```python
obs = env.reset()
for key, value in obs.items():
  print(key, getattr(value, 'shape', ()), getattr(value, 'dtype', type(value)))
```

Typical causes:

- float pixels in `[0, 1]`: they bypass DreamerV2's `uint8 / 255 - 0.5`
  preprocessing; convert to `uint8` or deliberately configure/model the float
  input.
- channel-first `(C, H, W)`: `ResizeImage` interprets `C, H` as spatial axes;
  transpose before `GymWrapper`.
- rank-2 non-image matrix: `ResizeImage` treats it as an image; flatten it or
  make it rank 1 if it is proprioceptive data.
- same target size but wrong dtype: `ResizeImage` does not touch same-size
  entries, so correct the raw adapter.
- direct `common.Dummy()` output: known structural fixture mismatch; do not use
  it as a pixel dtype oracle.

## Invalid one-hot actions

`OneHotAction` accepts a vector only if it matches the exact one-hot vector
reconstructed from its `argmax` (within NumPy's `allclose` tolerance).

Accepted: `[0, 1, 0]` for a three-action environment.

Rejected: `[0.5, 0.5, 0]`, `[0, 0, 0]`, `[1, 1, 0]`, NaNs, or a wrong shape.

If the raw environment receives a vector instead of an integer, wrapper order
is wrong. The required order is raw Gym, `GymWrapper`, `ResizeImage`, then
`OneHotAction`, then `TimeLimit`. If malformed policy output reaches the
wrapper, fix the policy/distribution or action shape; do not insert a silent
`argmax` repair.

This release's one-hot space overrides `sample()` with a method that is not a
reliable standalone sampler. The native prefill path uses DreamerV2's
`RandomAgent`, which samples from its own one-hot distribution.

## Bounded, one-sided, or unbounded continuous actions

For dimensions with two finite bounds, normalized `-1`, `0`, and `1` should map
to the native low, midpoint, and high. `NormalizeAction` does not clip, so
values outside `[-1, 1]` can map outside native bounds.

For any dimension with an infinite bound, the wrapper advertises `[-1, 1]` but
passes the value through unchanged. It does not respect a finite one-sided
bound. If this is not the intended control semantics:

1. expose a finite normalized Box in the raw custom environment;
2. transform to physical commands inside `step()`;
3. validate/clamp there according to domain rules;
4. test all boundary values before training.

## TimeLimit fails or episode flags disagree

`TimeLimit.step()` before `reset()` raises `Must reset environment.` After the
configured duration it sets `is_last=True`, clears its internal step counter,
and requires reset before another step. It does not alter `is_terminal`.

If the raw Gym environment already has a time limit, ensure its old-API `info`
contains `is_terminal=False` on truncation. Avoid two unrelated limits unless
the shorter one is intentional and its episode semantics are tested.

## Asynchronous environment strategy

`common.Async` supports exactly `thread` and `process`; native configuration
also accepts `none` to avoid workers.

Use `none` first. It produces the clearest stack traces and is the safe native
choice for this release. The DreamerV2 2.2.0 native parallel branch contains an
evaluation-environment construction defect and can fail before workers are
usable when `envs_parallel` is not `none`. Treat native `thread`/`process` as a
known release limitation rather than repeatedly changing environment assets.

For controlled direct use of `common.Async`:

- construct the entire adapter/action/time-limit stack inside a zero-argument
  callable;
- use a cloudpickle-able callable;
- in process mode, ensure registrations, imports, ROMs, MuJoCo libraries, and
  file paths are visible after a spawned child imports the program;
- protect application entry points appropriately for spawn;
- avoid sharing a live emulator, renderer, or mutable space mapping across
  workers;
- resolve the returned reset/step promise, or let DreamerV2's driver resolve it;
- close workers and inspect the child stack trace wrapped by `Lost connection
  to environment worker` or `Error in environment process`.

Choose threads only for environments whose libraries and renderer are
thread-safe and where process isolation is unnecessary. Choose processes for
isolation after a single synchronous instance succeeds. Do not increase worker
count while diagnosing a one-environment contract failure.

## Native launcher finds no `configs.yaml`

The installed console command in this release derives its config location from
the launcher path and is known to fail. This is not an environment/task-name
problem. For the native workflow, use:

```bash
python -m dreamerv2.train --help
```

Then let the training sub-skill build the actual module command, GPU gate, and
log directory. Do not copy or link package source scripts into a runtime
working directory as a workaround.
