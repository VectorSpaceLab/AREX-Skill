# Custom Wrappers

Gymnasium wrapper subclasses let an agent modify an environment without editing the environment class. Keep wrapper behavior aligned with the public `Env.reset(*, seed=None, options=None)` and `Env.step(action) -> (observation, reward, terminated, truncated, info)` API.

## Base Classes

| Base class | Override | Use when |
| --- | --- | --- |
| `gymnasium.Wrapper` | `step`, `reset`, `render`, `close`, or metadata/properties | You need access to multiple outputs, `info`, rendering, side effects, or custom lifecycle behavior. |
| `gymnasium.ObservationWrapper` | `observation(self, observation)` | Only observations from `reset()` and `step()` change. |
| `gymnasium.ActionWrapper` | `action(self, action)` | Caller actions need conversion before reaching the inner env. |
| `gymnasium.RewardWrapper` | `reward(self, reward)` | Only scalar/array rewards change. |

Always call `super().__init__(env)` in `__init__` and update `self.observation_space` or `self.action_space` if your transform changes the public contract.

## ObservationWrapper Pattern

```python
import numpy as np
import gymnasium as gym
from gymnasium.spaces import Box

class RelativePosition(gym.ObservationWrapper):
    def __init__(self, env):
        super().__init__(env)
        self.observation_space = Box(low=-np.inf, high=np.inf, shape=(2,), dtype=np.float32)

    def observation(self, observation):
        return (observation["target"] - observation["agent"]).astype(np.float32)
```

Use this pattern when the original observation is a `Dict` or other structure but the agent should see derived features. The new `observation_space` must describe exactly what `observation()` returns.

## ActionWrapper Pattern

```python
import numpy as np
import gymnasium as gym
from gymnasium.spaces import Discrete

class DiscreteActions(gym.ActionWrapper):
    def __init__(self, env, actions):
        super().__init__(env)
        self.actions = [np.asarray(action, dtype=env.action_space.dtype) for action in actions]
        self.action_space = Discrete(len(self.actions))

    def action(self, action):
        return self.actions[int(action)]
```

Use this when the policy should operate in a different action domain than the base environment. Update `action_space` to the caller-facing domain, not the inner env's domain.

## RewardWrapper Pattern

```python
import numpy as np
import gymnasium as gym

class BoundedReward(gym.RewardWrapper):
    def __init__(self, env, low=-1.0, high=1.0):
        super().__init__(env)
        self.low = low
        self.high = high

    def reward(self, reward):
        return float(np.clip(reward, self.low, self.high))
```

Use `RewardWrapper` for reward-only transforms. If the new reward depends on `info`, the action, termination flags, or previous observations, use `Wrapper.step()` instead.

## Full Wrapper Pattern

```python
import gymnasium as gym

class InfoReward(gym.Wrapper):
    def __init__(self, env, distance_weight=1.0, control_weight=0.1):
        super().__init__(env)
        self.distance_weight = distance_weight
        self.control_weight = control_weight

    def step(self, action):
        observation, reward, terminated, truncated, info = self.env.step(action)
        if "reward_dist" in info and "reward_ctrl" in info:
            reward = self.distance_weight * info["reward_dist"] + self.control_weight * info["reward_ctrl"]
        return observation, reward, terminated, truncated, info
```

Use the full wrapper for transforms that need `info`, need to alter multiple return values, or need custom render/reset behavior. Preserve the five-value step return unless deliberately routing to migration utilities in `../environment-api/SKILL.md`.

## Transform Wrapper Shortcuts

For simple callables, prefer built-ins over new classes:

```python
from gymnasium.wrappers import TransformAction, TransformObservation, TransformReward

env = TransformObservation(env, lambda obs: obs.astype("float32") / 255.0, observation_space=new_obs_space)
env = TransformAction(env, lambda action: action * 0.5, action_space=new_action_space)
env = TransformReward(env, lambda reward: reward / 100.0)
```

`TransformObservation` and `TransformAction` require a public space argument when the transform changes the contract. Passing the old space for a changed shape/dtype/bounds is a bug that will surface later in `contains`, model initialization, or wrappers such as `FlattenObservation`.

## Authoring Checklist

- Verify the wrapper subclasses the narrowest useful base class.
- Call `super().__init__(env)` before using wrapper properties.
- Update `observation_space`, `action_space`, or `metadata` when output contracts change.
- Keep `reset()` returning `(observation, info)` and `step()` returning `(observation, reward, terminated, truncated, info)`.
- Preserve or intentionally update `info` keys; avoid overwriting `RecordEpisodeStatistics`'s `"episode"` key.
- Seed via the underlying env reset/action spaces; wrappers should not introduce untracked randomness unless documented.
- Run one reset/step and assert `env.observation_space.contains(obs)` or inspect why containment is intentionally impossible.

## Smoke Script

Run the bundled script to verify a safe custom-wrapper chain:

```bash
python sub-skills/wrappers-recording/scripts/wrapper_smoke.py
python sub-skills/wrappers-recording/scripts/wrapper_smoke.py --mode transform
```

The script uses only base Gymnasium plus NumPy and avoids optional media, Atari, Box2D, MuJoCo, JAX, or Torch dependencies.
