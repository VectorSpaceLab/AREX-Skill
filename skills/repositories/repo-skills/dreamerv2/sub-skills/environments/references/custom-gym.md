# Custom Gym integration

Use the public Python API for custom environments. It accepts a Gym environment
object and internally applies:

```text
GymWrapper -> ResizeImage -> OneHotAction or NormalizeAction -> TimeLimit
```

Do not pre-apply those DreamerV2 wrappers before calling the API. Do apply any
environment-specific observation wrapper that is required to produce stable
numeric arrays.

## Legacy Gym contract

DreamerV2 2.2.0 expects the Gym 0.23-style API:

```python
observation = env.reset()
observation, reward, done, info = env.step(action)
```

The environment must expose `observation_space` and `action_space`. An
observation may be a numeric array or a mutable dictionary of numeric arrays.
The action may be a scalar discrete value, a continuous array, or a dictionary;
the standard DreamerV2 path is simplest with one scalar/array action.

If `done=True` because of a true absorbing state, either omit
`info['is_terminal']` or set it to true. If `done=True` only because of a time
limit, set `info['is_terminal']=False`.

## Dict observations with bounded continuous actions

This environment demonstrates the exact difficult case of a resized image,
proprioception vector, finite asymmetric action bounds, and separate terminal
versus time-limit signals:

```python
import gym
import numpy as np


class DictContinuousEnv(gym.Env):

  def __init__(self):
    self.observation_space = gym.spaces.Dict({
        'image': gym.spaces.Box(
            0, 255, shape=(48, 48, 3), dtype=np.uint8),
        'proprio': gym.spaces.Box(
            -np.inf, np.inf, shape=(4,), dtype=np.float32),
    })
    self.action_space = gym.spaces.Box(
        low=np.array([-2.0, -0.5], np.float32),
        high=np.array([2.0, 0.5], np.float32),
        dtype=np.float32,
    )
    self._rng = np.random.RandomState(0)
    self._step = 0
    self._state = np.zeros(4, np.float32)

  def seed(self, seed=None):
    self._rng = np.random.RandomState(seed)
    return [seed]

  def _obs(self):
    image = np.zeros((48, 48, 3), np.uint8)
    image[..., 0] = np.uint8(np.clip(127 + 20 * self._state[0], 0, 255))
    return {'image': image, 'proprio': self._state.copy()}

  def reset(self):
    self._step = 0
    self._state = self._rng.uniform(-0.1, 0.1, 4).astype(np.float32)
    return self._obs()

  def step(self, action):
    action = np.asarray(action, np.float32)
    if not self.action_space.contains(action):
      raise ValueError(f'Action outside native bounds: {action}')
    self._step += 1
    self._state[:2] += 0.05 * action
    reward = -float(np.square(self._state).sum())
    terminal = bool(np.linalg.norm(self._state) > 10.0)
    truncated = self._step >= 25
    done = terminal or truncated
    info = {'is_terminal': terminal}
    return self._obs(), reward, done, info
```

The API's `ResizeImage` changes `image` to `(64, 64, 3) uint8` under the default
render size and leaves `(4,) float32` `proprio` unchanged. `NormalizeAction`
exposes both policy dimensions as `[-1, 1]`; normalized zero maps to native
`[0.0, 0.0]` for these symmetric bounds.

Inspect the wrapped contract without starting a training loop:

```python
import numpy as np
from dreamerv2 import common

raw = DictContinuousEnv()
env = common.GymWrapper(raw)
env = common.ResizeImage(env, size=(64, 64))
env = common.NormalizeAction(env)
env = common.TimeLimit(env, duration=10)

assert env.obs_space['image'].shape == (64, 64, 3)
assert env.obs_space['image'].dtype == np.uint8
assert env.obs_space['proprio'].shape == (4,)
assert env.act_space['action'].shape == (2,)
np.testing.assert_allclose(env.act_space['action'].low, [-1, -1])
np.testing.assert_allclose(env.act_space['action'].high, [1, 1])

obs = env.reset()
assert obs['is_first'] and not obs['is_last'] and not obs['is_terminal']
assert obs['image'].shape == (64, 64, 3)
assert obs['image'].dtype == np.uint8

obs = env.step({'action': np.array([0.0, 0.0], np.float32)})
assert not obs['is_first']
```

A complete run passes the raw environment, not the manually wrapped one:

```python
import dreamerv2.api as dv2

config = dv2.defaults.update({
    'logdir': '~/logdir/dict_continuous',
    'time_limit': 25,
})
dv2.train(DictContinuousEnv(), config)
```

Before running that call, use the training sub-skill to select bounded run
settings and prove the TensorFlow/runtime requirements. Use the configuration
sub-skill for further updates and flag parsing.

## Unbounded and one-sided actions

`NormalizeAction` only applies finite-bound scaling when *both* bounds of a
dimension are finite. For any unbounded or one-sided dimension, it advertises
`[-1, 1]` and passes the submitted normalized value through unchanged.

If a physical command needs an unbounded transform, keep DreamerV2's visible
space finite and transform inside the raw environment:

```python
class SquashedCommandEnv(DictContinuousEnv):

  def __init__(self):
    super().__init__()
    self.action_space = gym.spaces.Box(-1, 1, (2,), dtype=np.float32)

  def step(self, action):
    action = np.asarray(action, np.float32)
    if not self.action_space.contains(action):
      raise ValueError(action)
    physical = np.arctanh(np.clip(action, -0.999, 0.999))
    # Apply `physical` to the simulator here, while retaining the same
    # observation and lifecycle contract.
    return self._step_physical(physical)

  def _step_physical(self, physical):
    raise NotImplementedError('Connect the physical command to the simulator')
```

Do not advertise `(-inf, inf)` and assume DreamerV2 will invent this transform.
Do not advertise a one-sided native bound and assume the wrapper clips it.

## Modern reset/step compatibility

Prefer Gym 0.23.1 and an environment version that supports its legacy API. If a
compatible `gym` environment only returns the modern API, place this shim
around it before passing it to DreamerV2:

```python
import gym


class LegacyStepAPI(gym.Wrapper):

  def reset(self, **kwargs):
    result = self.env.reset(**kwargs)
    if isinstance(result, tuple) and len(result) == 2:
      obs, info = result
      if isinstance(info, dict):
        return obs
    return result

  def step(self, action):
    result = self.env.step(action)
    if len(result) == 5:
      obs, reward, terminated, truncated, info = result
      info = dict(info)
      info.setdefault('is_terminal', bool(terminated))
      return obs, reward, bool(terminated or truncated), info
    if len(result) == 4:
      return result
    raise ValueError(f'Expected 4 or 5 step values, got {len(result)}')
```

This preserves `is_terminal=False` for pure truncation. It does not guarantee
compatibility with Gymnasium-only spaces, registries, wrappers, or render
semantics; mixing `gym` and `gymnasium` object families is outside the verified
package contract.

## MiniGrid-style image recipe

An era-compatible MiniGrid environment commonly starts with a dict observation
containing an image plus non-pixel metadata. Convert it to an RGB observation
and remove unsupported text values before giving it to DreamerV2. For example,
with versions that provide these wrappers:

```python
import gym
import gym_minigrid
import dreamerv2.api as dv2

raw = gym.make('MiniGrid-DoorKey-6x6-v0')
raw = gym_minigrid.wrappers.RGBImgPartialObsWrapper(raw)
raw = gym_minigrid.wrappers.ImgObsWrapper(raw)  # numeric image only

obs = raw.reset()
assert str(obs.dtype) == 'uint8' and obs.ndim == 3 and obs.shape[-1] in (1, 3)

config = dv2.defaults.update({'logdir': '~/logdir/minigrid'})
dv2.train(raw, config)
```

Wrapper names and environment IDs changed in later MiniGrid releases. Inspect
the actual reset result and space instead of copying a current `minigrid`
example into this legacy runtime.

## Reject malformed discrete actions and prove ordering

This synthetic test exercises `OneHotAction` without an emulator:

```python
import gym
import numpy as np
from dreamerv2 import common


class DiscreteSink:
  act_space = {'action': gym.spaces.Discrete(3)}

  def step(self, action):
    self.received = action
    return {'received': action['action']}

  def reset(self):
    return {}


sink = DiscreteSink()
env = common.OneHotAction(sink)
assert env.act_space['action'].shape == (3,)

env.step({'action': np.array([0, 1, 0], np.float32)})
assert sink.received['action'] == 1

bad = np.array([0.5, 0.5, 0.0], np.float32)
try:
  env.step({'action': bad})
except ValueError as exc:
  assert 'Invalid one-hot action' in str(exc)
else:
  raise AssertionError('Malformed one-hot action was accepted')
```

For a raw Gym discrete environment the full order is:

```python
env = common.GymWrapper(raw_discrete_env)
env = common.ResizeImage(env, (64, 64))
env = common.OneHotAction(env)
env = common.TimeLimit(env, duration)
```

Applying `OneHotAction` directly to `raw_discrete_env` is wrong because raw Gym
exposes `action_space`, not DreamerV2's dictionary `act_space`.
