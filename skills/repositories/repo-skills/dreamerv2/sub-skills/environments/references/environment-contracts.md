# Environment contracts

## Core protocol

DreamerV2's internal environment protocol is intentionally smaller than Gym.
An adapted environment exposes two mappings:

```python
env.obs_space  # str -> gym.Space
env.act_space  # str -> gym.Space
```

`reset()` and `step(action_dict)` return mutable dictionaries. Every
observation dictionary contains these lifecycle entries:

| Key | Declared space | Reset | Ordinary step | Meaning |
|---|---|---:|---:|---|
| `reward` | scalar `Box(-inf, inf)`, `float32` | `0.0` | scalar reward | reward caused by the action |
| `is_first` | scalar boolean `Box(0, 1)` | `True` | `False` | recurrent-state reset marker |
| `is_last` | scalar boolean `Box(0, 1)` | `False` | termination or truncation | episode boundary |
| `is_terminal` | scalar boolean `Box(0, 1)` | `False` | true termination only | zero-continuation marker |

A time-limit boundary must set `is_last=True` while preserving
`is_terminal=False`. A true terminal state normally sets both to true. The
model derives its discount input from `is_terminal`, not from `is_last`, so
conflating truncation and termination changes the learning target.

The driver converts floating arrays to `float32`, signed integer arrays to
`int32`, and `uint8` arrays to `uint8` before replay storage. The declared
spaces and direct environment outputs should still agree; relying on driver
conversion hides adapter defects during standalone tests.

At reset, the driver also records a zero action with the exact shape advertised
by every action-space entry. Keep shapes static across reset and step.

## Observation dtype and shape rules

DreamerV2 treats dtypes semantically:

- `uint8` observations are cast to the active compute dtype, divided by 255,
  and shifted by `-0.5`.
- `int32` observations are cast to the compute dtype without pixel scaling.
- floating observations are retained as numeric features.
- keys beginning with `log_` bypass model preprocessing and are for logging.
- image-like inputs use channel-last shapes `(height, width, channels)`.

Use `uint8` `[0, 255]` for pixels and Atari RAM. Use `float32` for vectors such
as position, velocity, or a custom `proprio` feature. A normalized float image
is not automatically shifted like a `uint8` image and therefore changes the
input distribution.

`ResizeImage` selects every observation whose declared shape has more than one
dimension and whose first two dimensions differ from the requested size. It
uses nearest-neighbor Pillow resizing and declares the result as `uint8`
`[0, 255]`. Consequences:

1. Give image tensors channel-last layout before this wrapper.
2. Do not put arbitrary rank-2 matrices in the observation dictionary unless
   they are intended to be resized as images.
3. A same-size image is not converted; its original dtype passes through.
4. `ResizeImage.obs_space` mutates the mapping returned by its inner adapter,
   so build each environment/wrapper stack independently rather than sharing a
   mutable space dictionary across workers.

## Native task parsing

The native training module evaluates:

```python
suite, task = config.task.split('_', 1)
```

The first underscore is mandatory. The supported suite tokens are `dmc`,
`atari`, and `crafter`.

DMC evaluates a second first-underscore split on the suite-specific remainder:

```python
domain, task = dmc_name.split('_', 1)
```

Examples:

| Config task | Suite adapter input | Interpretation |
|---|---|---|
| `dmc_walker_walk` | `walker_walk` | domain `walker`, task `walk` |
| `dmc_cup_catch` | `cup_catch` | special alias to domain `ball_in_cup`, task `catch` |
| `dmc_manip_reach_site` | `manip_reach_site` | manipulation loader receives `reach_site_vision` |
| `dmc_locom_rodent_maze_forage` | `locom_rodent_maze_forage` | invokes matching locomotion example factory |
| `atari_james_bond` | `james_bond` | adapter aliases the game to `jamesbond` |
| `crafter_reward` | `reward` | shaped/default reward enabled |
| `crafter_noreward` | `noreward` | reward disabled for training, enabled for evaluation |

`dmc_ball_in_cup_catch` is not equivalent to `dmc_cup_catch`; the second split
would treat `ball` as the domain. Crafter accepts exactly `reward` or
`noreward` because the adapter validates against those tokens.

## Suite schemas

### DMC

`common.DMC(name, action_repeat=1, size=(64, 64), camera=None)` exposes:

- `image`: `(height, width, 3)`, `uint8`, `[0, 255]`.
- every nonempty entry in the DM Control observation spec.
- the four lifecycle keys.
- `action`: a `float32` Box using the DM Control action minimum and maximum.

DM Control observation entries with shape `(0,)` are omitted. Native
`float64` observation specs are advertised as `float32`; native `uint8` specs
stay `uint8`. The DreamerV2 driver converts returned floating arrays to
`float32` before storage.

The adapter sets `MUJOCO_GL=egl`, selects a task-dependent default camera when
`camera` is `None` or `-1`, repeats each action, sums rewards, stops repetition
at the environment's last time step, and uses `discount == 0` for
`is_terminal`. It asserts that actions are finite and that DM Control discount
is exactly 0 or 1.

DMC is wrapped by `NormalizeAction` before `TimeLimit`.

### Atari

`common.Atari(name, action_repeat=4, size=(84, 84), grayscale=True, ...)`
requires a square render size and exposes:

- `image`: `(height, width, 1)` for grayscale or `(height, width, 3)` for RGB,
  `uint8`, `[0, 255]`.
- `ram`: `(128,)`, `uint8`, `[0, 255]`.
- the four lifecycle keys.
- `action`: the emulator's `gym.spaces.Discrete` space.

The adapter constructs the era Gym `AtariEnv` directly, applies
`AtariPreprocessing`, and supports no-op reset, action repeat, life-loss
handling, sticky actions, and full/minimal action sets. Its terminal signal
sets both `is_last` and `is_terminal`. ROM installation is an external asset
gate, independent of importing Gym.

Atari is wrapped by `OneHotAction` before `TimeLimit`.

### Crafter

`common.Crafter(outdir=None, reward=True, seed=None)` exposes:

- `image`: exactly the shape/dtype advertised by the installed
  `crafter.Env.observation_space` (the compatible release provides RGB pixel
  observations; verify it at runtime rather than hard-coding an unprobed
  version).
- the four lifecycle keys.
- `log_reward`: scalar `float32`.
- one scalar `int32` `log_achievement_<name>` key for every Crafter
  achievement.
- `action`: Crafter's discrete action space.

`is_terminal` comes from `info['discount'] == 0`; `is_last` comes from the
Crafter `done` value. The recorder saves statistics and may write under the
training log directory. The native module requires `action_repeat == 1`.

Crafter is wrapped by `OneHotAction` before `TimeLimit`.

### Dummy

`common.Dummy()` advertises `(64, 64, 3) uint8` image observations and a
six-dimensional `float32` action Box in `[-1, 1]`. It never returns a last or
terminal state. Its zero image is created without an explicit dtype, so the
direct output is floating point despite the advertised `uint8` space. Treat it
as a structural smoke fixture only.

## Generic GymWrapper

`common.GymWrapper(env, obs_key='image', act_key='action')` adapts the legacy
Gym API:

```python
obs = env.reset()
obs, reward, done, info = env.step(action)
```

If the observation space is not a `gym.spaces.Dict`, it becomes
`{obs_key: observation}`. A dict observation is retained and augmented in
place. If the action space is not a dict, it becomes
`{act_key: action_space}`; the wrapper extracts that key before calling the
raw environment.

The old four-item step contract is mandatory. `done` becomes `is_last`, and
`info.get('is_terminal', done)` becomes `is_terminal`. Therefore a custom
legacy environment should set `info['is_terminal'] = False` for a time-limit
truncation. A compatibility shim for the modern `(obs, info)` reset and
five-item step API is provided in [custom Gym integration](custom-gym.md).

The wrapper only adds protocol keys; it does not resize, render, normalize
pixels, or change actions. The public API performs those later wrappers.

## Action wrappers

### OneHotAction

The inner principal action space must have `.n`. The wrapper advertises a
`float32` Box with shape `(n,)`, low 0, high 1, and an added `.n` attribute for
DreamerV2's policy distribution. On step it:

1. finds `argmax`;
2. reconstructs an exact one-hot reference;
3. compares the submitted vector using `numpy.allclose`;
4. raises `ValueError: Invalid one-hot action` on mismatch;
5. passes the integer index to the inner environment on success.

Reject all-zero vectors, soft distributions, multi-hot vectors, NaNs, and
wrong shapes. Use DreamerV2's `RandomAgent` for prefill; this release's custom
`space.sample()` override is not a reliable standalone sampling path.

### NormalizeAction

For each dimension where both native bounds are finite, the wrapper advertises
`[-1, 1]` and maps:

```text
native = (normalized + 1) / 2 * (high - low) + low
```

Dimensions with an infinite lower or upper bound are also advertised as
`[-1, 1]`, but the normalized value is passed through unchanged. Thus a
one-sided native bound is not enforced by this wrapper. Put the desired
physical transform and clipping in the custom environment if its true action
range is unbounded or one-sided.

The wrapper does not clip out-of-range submitted actions. Validate policy or
caller actions before forwarding them.

## ResizeImage, TimeLimit, and Async

`ResizeImage` belongs after `GymWrapper` and before action adaptation.
`TimeLimit(env, duration)` belongs outside action adaptation. A zero duration
disables the limit. It requires `reset()` before `step()`, marks only
`is_last=True` at the duration, and then requires another reset. It intentionally
does not set `is_terminal` at a time-limit boundary.

`common.Async(constructor, strategy)` takes a zero-argument, cloudpickle-able
constructor and supports exactly `thread` or `process`. Put the complete
wrapper construction inside that callable. Process mode uses a spawned worker,
so environment registration and required assets must be available in the child
process. By default `step()` and `reset()` return promises; DreamerV2's driver
resolves them. Always call `close()` or allow the registered exit handler to
join workers.
