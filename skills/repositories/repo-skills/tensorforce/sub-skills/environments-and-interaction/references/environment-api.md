# Environment API and custom environment contract

Tensorforce 0.6.x exposes the environment entry point as:

```python
from tensorforce import Environment
# equivalent public import in many examples:
# from tensorforce.environments import Environment

environment = Environment.create(
    environment=None,
    max_episode_timesteps=None,
    reward_shaping=None,
    remote=None,
    blocking=False,
    host=None,
    port=None,
    **kwargs,
)
```

## `Environment.create(...)` input forms

Use `Environment.create(...)` instead of directly handing raw environment objects to agents. The factory applies Tensorforce wrappers for max-timestep abort behavior, reward shaping, and remote execution.

Supported forms:

1. **Registry key string**: `environment='custom_cartpole'`, `'gym'`, `'openai_gym'`, `'ale'`, `'retro'`, `'osim'`, `'ple'`, `'vizdoom'`, `'carla'`, or aliases listed in `optional-environment-adapters.md`.
2. **Gym level string fallback**: an unknown string is tried as an importable module/class; if that fails it is passed to the Gym adapter as `level=<string>`. Example: `Environment.create(environment='CartPole-v1', max_episode_timesteps=500)` attempts Gym if no Tensorforce registry/module matches.
3. **Dictionary specification**: use `environment` or `type` for the adapter/class and include constructor keyword arguments in the same dictionary.
4. **JSON specification file**: a user-provided JSON file with the same keys as a dictionary spec. Keep the JSON in the user's project or experiment directory; do not require a Tensorforce source checkout file.
5. **Custom `Environment` object**: wraps an already constructed subclass instance.
6. **Custom `Environment` class**: instantiates the class with `**kwargs`, then wraps it. Use this for self-contained local classes.
7. **Importable module/class path**: a Python import path resolving to a Tensorforce `Environment` subclass or a `gym.Env` class/object.
8. **Gym `Env` object/class**: routes through the Gym adapter.

Examples:

```python
# Built-in Tensorforce custom CartPole.
env = Environment.create(environment='custom_cartpole', max_episode_timesteps=500)

# Gym adapter with explicit level.
env = Environment.create(environment='gym', level='CartPole-v1', max_episode_timesteps=500)

# Dictionary spec. Extra keys are constructor kwargs for the adapter/class.
env = Environment.create(dict(environment='gym', level='CartPole-v1', max_episode_timesteps=500))

# Custom class. The class must subclass tensorforce.Environment.
env = Environment.create(environment=MyEnvironment, max_episode_timesteps=100, seed=7)
```

## Custom `Environment` subclass checklist

A minimal custom environment should:

- Call `super().__init__()` in `__init__`.
- Implement `states(self)` and `actions(self)` and return Tensorforce space specs.
- Implement `reset(self)` and return the initial state in the exact shape/type declared by `states()`.
- Implement `execute(self, actions)` and return `(next_states, terminal, reward)`.
- Implement `close(self)` if external resources, files, windows, simulators, sockets, or processes need cleanup.
- Implement `max_episode_timesteps(self)` only if the environment has a natural fixed episode limit. Otherwise pass `max_episode_timesteps=...` to `Environment.create(...)` or `Runner(...)`.

Minimal example:

```python
import numpy as np
from tensorforce import Environment

class CounterEnvironment(Environment):
    def __init__(self, goal=10):
        super().__init__()
        self.goal = int(goal)
        self.position = None

    def states(self):
        return dict(type='float', shape=(2,), min_value=0.0, max_value=float(self.goal))

    def actions(self):
        # Discrete scalar action in {0, 1, 2}; Tensorforce 0.6.x examples use num_values.
        return dict(type='int', shape=(), num_values=3)

    def reset(self):
        self.position = 0.0
        return np.asarray([self.position, float(self.goal)], dtype=np.float32)

    def execute(self, actions):
        action = int(np.asarray(actions).item())
        self.position = float(np.clip(self.position + (action - 1), 0.0, self.goal))
        terminal = self.position >= self.goal
        reward = 1.0 if action == 2 else -0.1
        return np.asarray([self.position, float(self.goal)], dtype=np.float32), terminal, reward
```

Then wrap it:

```python
env = Environment.create(environment=CounterEnvironment, goal=5, max_episode_timesteps=20)
states = env.reset()
next_states, terminal, reward = env.execute(actions=2)
env.close()
```

## State and action specifications

Tensorforce accepts a single tensor spec or a nested dictionary of named specs.

Common scalar/vector specs:

```python
# Float vector with bounds.
dict(type='float', shape=(4,), min_value=-1.0, max_value=1.0)

# Discrete scalar with values 0..2.
dict(type='int', shape=(), num_values=3)

# Boolean vector.
dict(type='bool', shape=(5,))

# Multi-component state.
dict(
    observation=dict(type='float', shape=(8,)),
    inventory=dict(type='int', shape=(3,), num_values=10),
)
```

Practical rules:

- `type` is usually one of `'bool'`, `'int'`, or `'float'`.
- `shape=()` means scalar; omit shape only when the API example you are following does so for scalar discrete spaces.
- Integer specs in Tensorforce 0.6.x public API usage typically use `num_values` for the number of discrete values.
- For a single unnamed state spec, return a bare array/scalar from `reset()`/`execute()`. If returning a dict for a single state, use key `state` plus optional mask keys.
- For a multi-component state spec, returned dict keys must match the spec keys, except action masks may be added with names ending in `_mask`.
- For a single unnamed action spec, `execute(actions)` receives a scalar/array action. For multi-action specs, it receives a dict keyed by action names.

## Terminal values and max episode timesteps

Tensorforce distinguishes three terminal meanings:

- `False` or `0`: episode continues.
- `True` or `1`: natural terminal state.
- `2`: abort terminal, usually because a time limit was reached.

If an environment created through `Environment.create(..., max_episode_timesteps=N)` returns non-terminal at timestep `N`, Tensorforce's wrapper converts the terminal to `2`. This matters for reward estimation: an abort due to time limit is not treated the same as a true task terminal.

Guidelines:

- In a custom environment, return `True`/`1` only for real task termination.
- Return `False`/`0` for ordinary continuation and let the wrapper emit `2` for configured time limits.
- If the simulator itself can tell true termination from timeout, map true termination to `1` and timeout/truncation to `2`.
- If no max episode length is set anywhere, some agent hyperparameters and runner workflows may lack the horizon information they expect.

## Reward shaping

`reward_shaping` can be either a callable or a trusted string expression.

Callable form:

```python
def shape_reward(states, actions, terminal, reward, next_states):
    shaped = reward - 0.01
    return shaped

env = Environment.create(environment=MyEnvironment, reward_shaping=shape_reward)
```

A callable may also return `(reward, terminal)` if shaping should change the terminal signal.

String expression form:

```python
env = Environment.create(
    environment=MyEnvironment,
    reward_shaping='reward - 0.01 if not terminal else reward'
)
```

The string expression is evaluated with variables `states`, `actions`, `terminal`, `reward`, `next_states`, `math`, `np`, and `random`. Treat it as trusted-code configuration, not as user-supplied untrusted input.

## Close and lifecycle

Always call `close()` when finished. This is essential for Gym render windows, CARLA/PLE/ViZDoom resources, multiprocessing children, socket connections, and any environment wrapping files or devices.

Recommended lifecycle:

```python
env = Environment.create(environment=MyEnvironment, max_episode_timesteps=100)
try:
    states = env.reset()
    terminal = 0
    while terminal == 0:
        actions = choose_action_somehow(states)
        states, terminal, reward = env.execute(actions=actions)
finally:
    env.close()
```
