---
name: environments
description: "Operate DreamerV2 2.2.0 environment adapters for DMC, Atari,
  Crafter, and legacy Gym or custom environments, including task naming, wrapper
  order, schemas, assets, and dependency diagnosis."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# DreamerV2 Environments

Use this sub-skill to select or adapt an environment for DreamerV2 2.2.0 and
to verify the environment-facing contract before a costly run. This package is
from the TensorFlow 2.6 and Gym 0.23 era; do not silently substitute a modern
Gymnasium contract.

Route training commands, GPU/precision checks, replay, and checkpoints to
[training](../training/SKILL.md). Route preset and flag composition to
[configuration](../configuration/SKILL.md), and metrics or videos to
[evaluation](../evaluation/SKILL.md).

## Choose the integration path

| Need | Path | First adapter |
|---|---|---|
| DM Control pixels or proprioception | native `dmc_<domain>_<task>` | `common.DMC` |
| Atari pixels and RAM | native `atari_<game>` | `common.Atari` |
| Crafter reward/no-reward | native `crafter_reward` or `crafter_noreward` | `common.Crafter` |
| User-created or registered Gym environment | `dreamerv2.api.train(env, ...)` | internal `common.GymWrapper` |
| Contract-only smoke fixture | direct `common.Dummy()` | none |

Read [environment contracts](references/environment-contracts.md) before
constructing wrappers. Read [custom Gym integration](references/custom-gym.md)
for a dict-observation continuous-action recipe and strict one-hot test. Use
[environment troubleshooting](references/troubleshooting.md) for dependency,
ROM, rendering, API-version, shape, and asynchronous worker failures.

## Parse native task names exactly

The native module splits `config.task` once:

```text
<suite>_<suite-specific-task>
```

The separator is the first underscore. Valid examples include
`dmc_walker_walk`, `dmc_cup_catch`, `atari_pong`, `atari_james_bond`,
`crafter_reward`, and `crafter_noreward`. A missing underscore fails unpacking;
an unknown suite raises `NotImplementedError`. DMC then splits its remainder
once into domain and task. Use `cup_catch`, not `ball_in_cup_catch`, because the
adapter maps the special `cup` alias to DM Control's `ball_in_cup` domain.

Native environment selection exists only for DMC, Atari, and Crafter. A
custom Gym ID is not a fourth native suite; create it in Python and pass the
environment object to `dreamerv2.api.train`.

## Preserve the wrapper order

Native built-ins use:

```text
DMC     -> NormalizeAction -> TimeLimit
Atari  -> OneHotAction     -> TimeLimit
Crafter-> OneHotAction     -> TimeLimit
```

The public Python API applies:

```text
raw legacy Gym env
  -> GymWrapper
  -> ResizeImage
  -> OneHotAction if Discrete, otherwise NormalizeAction
  -> TimeLimit
```

Do not put `OneHotAction` or `NormalizeAction` before `GymWrapper`: those
wrappers require DreamerV2's dictionary `act_space`. Keep `TimeLimit`
outermost so a truncation sets `is_last=True` without falsely changing
`is_terminal`. If asynchronous execution is needed, construct the complete
wrapped environment inside each worker, then put `common.Async` outside it.

## Enforce the minimum observation contract

Every reset and step result must be a mutable mapping containing:

- `reward`: scalar numeric; reset value is `0.0`.
- `is_first`: scalar boolean; true only on reset transitions.
- `is_last`: scalar boolean; true at episode end or time-limit truncation.
- `is_terminal`: scalar boolean; true only when continuation should be zero.

Image observations are channel-last arrays. Pixels must be `uint8` in
`[0, 255]`; the model converts `uint8` to floating point and scales it to
`[-0.5, 0.5]`. Ordinary vector/proprioceptive values should be `float32`.
Do not pre-normalize pixels to floats while advertising a `uint8` space.

Use the suite-specific schema table in
[environment contracts](references/environment-contracts.md). In particular,
Atari grayscale is `(H, W, 1)`, Atari RAM is `(128,) uint8`, and DMC renders
`(H, W, 3) uint8` while retaining nonempty proprioceptive entries.

## Enforce the action contract

- Discrete: `OneHotAction` exposes `(n,) float32` values and accepts only a
  valid one-hot vector. It converts the hot index back to a scalar action.
- Continuous: `NormalizeAction` exposes `float32` actions. Dimensions whose
  lower and upper bounds are both finite map linearly from `[-1, 1]` to the
  native bounds.
- Unbounded or one-sided continuous dimensions are exposed as `[-1, 1]` and
  passed through unchanged. If that range is unsuitable, place the nonlinear
  or physical scaling inside the custom environment and advertise finite
  bounds to DreamerV2.
- Dict action spaces are retained by `GymWrapper`, but the built-in API only
  chooses and wraps the key named `action`; prefer one principal `action`
  entry unless the policy/configuration has been deliberately extended.

Never repair a soft probability vector with `argmax` before validation. A
vector such as `[0.5, 0.5, 0.0]` is malformed and should raise the adapter's
`Invalid one-hot action` error.

## Validate before training

1. Instantiate exactly one environment without launching training.
2. Inspect `obs_space` and `act_space`; confirm declared shape, dtype, bounds,
   and the principal `action` key.
3. Call `reset()` and assert the four lifecycle keys and suite data keys.
4. Call one valid `step()` and compare every returned array with its declared
   space. Distinguish truncation (`is_last`, not terminal) from termination.
5. For discrete actions, verify one valid vector and one malformed vector.
6. For continuous actions, test `-1`, `0`, and `1` against finite native bounds.
7. Only then perform the GPU and runtime gates documented by
   [training](../training/SKILL.md).

The built-in `Dummy` is useful for import/control-flow smoke tests only. Its
returned zero image does not faithfully preserve its declared `uint8` pixel
dtype, and it never ends an episode; do not use it as the image-contract gold
standard.

## Respect dependency and asset boundaries

Environment construction and full training readiness are different gates.
The package metadata lists all suites as dependencies, but the suite modules
are imported lazily by their adapters:

- Base Gym wrapper: legacy `gym` plus NumPy; image resizing also needs Pillow.
- Atari: Gym Atari integration, `atari_py`, and separately licensed/imported
  ROM assets.
- DMC: `dm_control`, a compatible MuJoCo runtime, and working EGL/OpenGL for
  rendered observations; old runtimes may also require a MuJoCo key.
- Crafter: `crafter` and its packaged/runtime assets.
- Custom Gym: the environment's own package, registrations, files, and system
  libraries remain the caller's responsibility.

Native `python -m dreamerv2.train` additionally needs the verified era stack
(TensorFlow 2.6.0, TensorFlow Probability 0.14.1, Gym 0.23.1) and a visible
GPU because the native module asserts one. The public API has no equivalent
GPU assertion, but it still loads the full TensorFlow agent and is not an
environment-only checker. Do not use the installed `dreamerv2` console command:
in this release its config lookup is launcher-path dependent. Use the module
route when the training sub-skill calls for the native entry point.
