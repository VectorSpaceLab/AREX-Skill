# Core Workflows

These recipes are self-contained patterns for building Acme core loops. They avoid backend-specific JAX/TF agent builders and focus on the `dm_env` + `Actor` + `EnvironmentLoop` boundary.

## 1. Adapt a Gym-Like Environment

Prefer an existing wrapper when the environment is an OpenAI Gym environment:

```python
import gym
from acme import specs
from acme import wrappers

raw_env = gym.make('CartPole-v0')
environment = wrappers.GymWrapper(raw_env)
environment = wrappers.SinglePrecisionWrapper(environment)
environment_spec = specs.make_environment_spec(environment)
```

Checklist:

1. Call `reset()` and verify it returns a `dm_env.TimeStep` whose `.first()` is true.
2. Compare `environment_spec.observations` with `reset_timestep.observation`.
3. Generate or sample an action compatible with `environment_spec.actions`.
4. Call `step(action)` and verify reward/discount dtypes match `reward_spec()` and `discount_spec()`.
5. Close the environment if the wrapped object owns external resources.

`GymWrapper` handles the older Gym API that returns `(observation, reward, done, info)` from `step()`. If the user's environment follows the newer API returning terminated/truncated separately, add a small adapter around the raw env before passing it to `GymWrapper`, or implement `dm_env.Environment` directly.

## 2. Implement a Minimal `dm_env.Environment`

A custom Acme environment must implement `reset`, `step`, and the four spec methods. This skeleton is useful when adapting a simulator that is not Gym-compatible:

```python
import dm_env
import numpy as np
from acme import specs

class CounterEnvironment(dm_env.Environment):
  def __init__(self, limit=5):
    self._limit = limit
    self._count = 0

  def reset(self):
    self._count = 0
    return dm_env.restart(np.array([self._count], dtype=np.float32))

  def step(self, action):
    del action
    self._count += 1
    observation = np.array([self._count], dtype=np.float32)
    reward = np.float32(1.0)
    if self._count >= self._limit:
      return dm_env.termination(reward, observation)
    return dm_env.transition(reward, observation)

  def observation_spec(self):
    return specs.Array((1,), np.float32, name='observation')

  def action_spec(self):
    return specs.DiscreteArray(2, dtype=np.int32, name='action')

  def reward_spec(self):
    return specs.Array((), np.float32, name='reward')

  def discount_spec(self):
    return specs.BoundedArray((), np.float32, minimum=0.0, maximum=1.0,
                              name='discount')
```

Debug the environment before adding an actor:

```python
env = CounterEnvironment()
print(env.observation_spec(), env.action_spec())
timestep = env.reset()
while not timestep.last():
  timestep = env.step(env.action_spec().generate_value())
```

## 3. Wire a Simple Actor to `EnvironmentLoop`

A minimal `Actor` implementation is enough to prove the loop, specs, logger, and observer plumbing before adding a real learner.

```python
from acme import core
from acme import specs
from acme import EnvironmentLoop
from acme.utils import loggers

class SpecActor(core.Actor):
  def __init__(self, environment_spec):
    self._action_spec = environment_spec.actions
    self.num_updates = 0

  def select_action(self, observation):
    del observation
    return self._action_spec.generate_value()

  def observe_first(self, timestep):
    del timestep

  def observe(self, action, next_timestep):
    del action, next_timestep

  def update(self, wait=False):
    del wait
    self.num_updates += 1

environment_spec = specs.make_environment_spec(environment)
actor = SpecActor(environment_spec)
logger = loggers.TerminalLogger(label='smoke', print_fn=print, time_delta=0.0)
loop = EnvironmentLoop(environment, actor, logger=logger)
steps = loop.run(num_episodes=1)
```

Use `should_update=False` for evaluation loops that should call `select_action` and `observe` but not `update`.

## 4. Add Counters, Loggers, and Observers

Acme logs one dictionary per completed episode from `EnvironmentLoop.run()`.

```python
from acme.utils import counting
from acme.utils import loggers
from acme.utils import observers

counter = counting.Counter(prefix='actor')
logger = loggers.make_default_logger(
    'environment_loop', save_data=False, time_delta=0.0, print_fn=print)
observer_list = [
    observers.ActionNormObserver(),
    observers.EnvInfoObserver(),
]
loop = EnvironmentLoop(
    environment,
    actor,
    counter=counter,
    logger=logger,
    observers=observer_list,
)
loop.run(num_episodes=3)
```

Notes:

- `Counter.increment(episodes=1, steps=episode_steps)` is called once per episode.
- `Counter.get_steps_key()` returns the step key passed to the default logger.
- `EnvInfoObserver` only records scalar values from `env.get_info()`; `GymWrapper` exposes the last Gym `info` dictionary through `get_info()`.
- `MeasurementObserver` can create many metrics for high-dimensional observations; reserve it for compact observation vectors.
- `CSVLogger` fixes columns from the first write, so make sure important observer keys are present in the first episode or use a custom logger during exploratory debugging.

If `acme.utils.loggers` cannot be imported because optional JAX is missing, use a local logger object with the same tiny protocol while debugging:

```python
class PrintLogger:
  def write(self, data):
    print(data)

  def close(self):
    pass
```

## 5. Compose Wrappers Safely

Use `wrappers.wrap_all` when wrapper order matters and you want the order to be explicit.

```python
from acme import wrappers

environment = wrappers.wrap_all(raw_dm_env, [
    wrappers.SinglePrecisionWrapper,
    lambda env: wrappers.CanonicalSpecWrapper(env, clip=True),
])
```

Order guidelines:

- Put adapters from non-`dm_env` APIs first, e.g. `GymWrapper(raw_gym_env)`, before ordinary `dm_env` wrappers.
- Put dtype normalization (`SinglePrecisionWrapper`) before code that assumes float32/int32 observations, rewards, or actions.
- Use `CanonicalSpecWrapper` only for bounded continuous action specs; it changes the public action scale to `[-1, 1]` and rescales before calling the wrapped environment.
- Use `StepLimitWrapper` or environment-native time limits consistently; duplicate time-limit wrappers can make termination/truncation debugging confusing.
- Keep Atari/OpenSpiel wrappers behind optional dependency checks because their imports may be absent in a core install.

## 6. Debug a Spec or Action Mismatch

Use this sequence before changing agent code:

```python
environment_spec = specs.make_environment_spec(environment)
print('observation spec:', environment_spec.observations)
print('action spec:', environment_spec.actions)
print('reward spec:', environment_spec.rewards)
print('discount spec:', environment_spec.discounts)

timestep = environment.reset()
print('reset observation:', type(timestep.observation), getattr(timestep.observation, 'shape', None))

action = environment_spec.actions.generate_value()
print('generated action:', action, getattr(action, 'dtype', None))
timestep = environment.step(action)
print('step type:', timestep.step_type, 'reward:', timestep.reward, 'discount:', timestep.discount)
```

Then check:

- The actor returns the same nested structure as `environment_spec.actions`.
- Arrays use the expected dtype (`SinglePrecisionWrapper` can normalize common float64/int64 outputs).
- Bounded actions respect min/max; use `spec.validate(action)` for individual `dm_env` specs.
- The environment does not require reset before the next step; `GymWrapper` automatically resets on the next `step()` after `done`.

## 7. Use a Core Smoke Test Before Backend Work

Before involving JAX, TensorFlow/Sonnet, Reverb, or Launchpad, prove the core loop:

1. Import `acme`, `acme.specs`, and `acme.core`.
2. Build or wrap the environment.
3. Create `environment_spec = specs.make_environment_spec(environment)`.
4. Run one episode with a spec-generated-action actor and a simple logger.
5. Add observers and wrappers one at a time.
6. Only then route to the backend-specific sub-skill for real policy networks, replay, or distributed execution.

The bundled script `scripts/check_core_imports.py --json` can be run as an import probe before this smoke test. It reports core import failures, optional backend availability, and selected signatures without running real RL workloads.
