# Core API Contracts

Acme core is intentionally small: environments follow `dm_env.Environment`, actors implement `acme.core.Actor`, and `EnvironmentLoop` coordinates their interaction. The core package installed from `dm-acme==0.4.1` has minimal required dependencies (`absl-py`, `dm-env`, `dm-tree`, `numpy`, `pillow`, `typing-extensions`), while many real agents and some utility imports may still depend on optional JAX, TensorFlow, Reverb, Launchpad, Gym, Atari, or OpenSpiel packages.

## Public Core Exports

`import acme` exposes these core surfaces:

| Surface | Contract |
| --- | --- |
| `acme.Actor` | Alias of `acme.core.Actor`. Implement to select actions, observe timesteps, and update local state/variables. |
| `acme.Learner` | Alias of `acme.core.Learner`. Implement `step()`; inherit `run(num_steps=None)` unless custom scheduling is needed. |
| `acme.Saveable` | Interface with `save()` and `restore(state)`. |
| `acme.VariableSource` | Interface with `get_variables(names)` returning a list of nested numpy-like variable collections. |
| `acme.Worker` | Interface with `run()`. |
| `acme.EnvironmentLoop` | Alias of `acme.environment_loop.EnvironmentLoop`. |
| `acme.specs` | Module exposing `Array`, `BoundedArray`, `DiscreteArray`, `EnvironmentSpec`, and `make_environment_spec`. |
| `acme.make_environment_spec` | Alias of `acme.specs.make_environment_spec(environment)`. |

## Specs

Use `acme.specs` to describe the values exchanged with a `dm_env` environment.

| API | Signature / shape | Notes |
| --- | --- | --- |
| `specs.Array` | `Array(shape, dtype, name=None)` | Alias of `dm_env.specs.Array`. Describes an unconstrained array. |
| `specs.BoundedArray` | `BoundedArray(shape, dtype, minimum, maximum, name=None)` | Alias of `dm_env.specs.BoundedArray`. Use for continuous bounded actions/observations. |
| `specs.DiscreteArray` | `DiscreteArray(num_values, dtype=np.int32, name=None)` in `dm_env` | Available through `acme.specs`. Useful for discrete action spaces. |
| `specs.EnvironmentSpec` | `EnvironmentSpec(observations, actions, rewards, discounts)` | NamedTuple collecting the four environment specs. |
| `specs.make_environment_spec(environment)` | `make_environment_spec(environment: dm_env.Environment) -> EnvironmentSpec` | Calls `environment.observation_spec()`, `action_spec()`, `reward_spec()`, and `discount_spec()`. |

For custom environments, make sure each emitted value is valid for its spec. For example, a scalar discrete action actor should return an integer-like value compatible with `DiscreteArray`, while a bounded continuous actor should return an array with the declared shape and dtype.

## Actor Interface

Implement `acme.core.Actor` when wiring an environment loop or creating a lightweight custom agent.

| Method | Signature | Called by `EnvironmentLoop` |
| --- | --- | --- |
| `select_action` | `select_action(observation) -> action` | Called once per non-terminal environment step with `timestep.observation`. |
| `observe_first` | `observe_first(timestep: dm_env.TimeStep)` | Called immediately after `environment.reset()` before the first action. |
| `observe` | `observe(action, next_timestep: dm_env.TimeStep)` | Called after `environment.step(action)`. |
| `update` | `update(wait: bool = False)` | Called after `observe()` only when `EnvironmentLoop(..., should_update=True)`. |

A minimal actor can ignore observations and return `environment_spec.actions.generate_value()` for smoke tests, but production actors should validate returned action dtype/shape against the action spec.

## Learner Interface

`acme.core.Learner` combines `VariableSource`, `Worker`, and `Saveable`.

| Method | Signature | Notes |
| --- | --- | --- |
| `step` | `step()` | Abstract. Implement one learner update. |
| `run` | `run(num_steps=None) -> None` | Provided implementation calls `step()` `num_steps` times, or forever when `num_steps is None`. |
| `get_variables` | `get_variables(names)` | Abstract via `VariableSource`; returns one variable collection per requested name. |
| `save` | `save()` | Inherited default raises `NotImplementedError`; override for checkpointable learners. |
| `restore` | `restore(state)` | Inherited default raises `NotImplementedError`; override with `save()`. |

Use this sub-skill to describe the interface only. Dataset consumption, adders, replay buffers, and backend-specific learner implementations belong to the data/backend sub-skills.

## EnvironmentLoop

`EnvironmentLoop` coordinates one `dm_env.Environment` and one `Actor`.

```python
from acme import EnvironmentLoop

loop = EnvironmentLoop(environment, actor)
steps_run = loop.run(num_episodes=10)
```

### Constructor

```python
EnvironmentLoop(
    environment,
    actor,
    counter=None,
    logger=None,
    should_update=True,
    label='environment_loop',
    observers=(),
)
```

| Argument | Meaning |
| --- | --- |
| `environment` | A `dm_env.Environment` with `reset()`, `step(action)`, and spec methods. |
| `actor` | An `acme.core.Actor` instance. |
| `counter` | Optional `acme.utils.counting.Counter`; defaults to a local counter. |
| `logger` | Optional `acme.utils.loggers.Logger`; defaults to `loggers.make_default_logger(label, steps_key=counter.get_steps_key())`. |
| `should_update` | When `True`, calls `actor.update()` after every environment step. Set `False` for evaluation-style loops. |
| `label` | Label used only when Acme creates the default logger. |
| `observers` | Sequence of `EnvLoopObserver` instances that add episode metrics. |

### Episode and run behavior

| Method | Behavior |
| --- | --- |
| `run_episode() -> loggers.LoggingData` | Resets the environment, calls `observe_first`, loops until `timestep.last()`, updates the actor, accumulates returns, updates the counter, merges observer metrics, and returns one metrics dictionary. |
| `run(num_episodes=None, num_steps=None) -> int` | Runs complete episodes until the selected bound is reached. The final episode may exceed `num_steps`; return value is actual environment steps executed. |

`run()` raises `ValueError('Either "num_episodes" or "num_steps" should be None.')` when both bounds are provided. Pass exactly one bound for finite runs, or neither for an unbounded worker loop.

Metrics emitted by `run_episode()` include at least `episode_length`, `episode_return`, `steps_per_second`, `env_reset_duration_sec`, `select_action_duration_sec`, `env_step_duration_sec`, `episodes`, and `steps`. `run()` also adds `episode_duration` before writing to the logger.

## OpenSpiel Loop Boundary

`acme.environment_loops.open_spiel_environment_loop.OpenSpielEnvironmentLoop` is a separate multi-agent loop for `acme.wrappers.open_spiel_wrapper.OpenSpielWrapper`. It requires the optional `pyspiel` package and currently supports turn-based sequential games; simultaneous move games raise `ValueError('Currently only supports sequential games.')`. Keep OpenSpiel-specific wrapper setup separate from ordinary single-environment `EnvironmentLoop` debugging.

## Wrappers

Common wrappers are exported from `acme.wrappers`.

| Wrapper / helper | Contract |
| --- | --- |
| `EnvironmentWrapper(environment)` | Base `dm_env.Environment` wrapper that forwards `step`, `reset`, specs, `close`, and unknown attributes to the wrapped environment. |
| `wrap_all(environment, wrappers)` | Applies wrapper callables in order: `environment = wrapper(environment)` for each wrapper. |
| `GymWrapper(gym_env)` | Adapts an OpenAI Gym environment to `dm_env.Environment`; converts Gym spaces into Acme/dm_env specs and stores last `info` for `get_info()`. Requires optional `gym`. |
| `GymAtariAdapter(gym_env)` | Gym Atari adapter exposing `(rgb_observation, lives)` and list-wrapped actions. Requires Gym/Atari dependencies. |
| `SinglePrecisionWrapper(environment)` | Converts float64 specs/values to float32 and int64 specs/values to int32. Leaves object/string specs unchanged. |
| `CanonicalSpecWrapper(environment, clip=False)` | Exposes bounded action specs as `[-1, 1]` while scaling actions back to the wrapped environment bounds in `step()`. |
| `StepLimitWrapper`, `ActionRepeatWrapper`, `DelayedRewardWrapper`, `FrameStackingWrapper`, `ConcatObservationWrapper`, `ObservationActionRewardWrapper`, `NoopStartsWrapper` | Episode/control and observation utilities; inspect constructor parameters in the installed package before use. |
| `AtariWrapper` | Atari preprocessing stack requiring Atari/Gym/ALE-style optional dependencies. |
| `OpenSpielWrapper` | Exported only when optional OpenSpiel import succeeds. |

`GymWrapper` converts `spaces.Discrete` to `specs.DiscreteArray`, `spaces.Box` to `specs.BoundedArray`, `spaces.MultiBinary`/`MultiDiscrete` to bounded specs, and tuple/dict spaces recursively. Unsupported spaces raise `ValueError('Unexpected gym space: ...')`.

## Logging, Counting, and Observers

| API | Contract |
| --- | --- |
| `counting.Counter(parent=None, prefix='', time_delta=1.0, return_only_prefixed=False)` | Tracks named counts and can periodically sync to a parent counter. `increment(**counts)` returns current counts; `get_steps_key()` returns `steps` or prefixed steps key. |
| `loggers.Logger` | Abstract base with `write(data)` and `close()`. |
| `loggers.NoOpLogger` | Logger that ignores writes; useful for tests or quiet evaluation. |
| `loggers.TerminalLogger(label='', print_fn=logging.info, serialize_fn=serialize, time_delta=0.0)` | Pretty-prints sorted key/value metrics; default writes every call. |
| `loggers.CSVLogger(directory_or_file='~/acme', label='', time_delta=0.0, add_uid=True, flush_every=30)` | Appends metrics to `logs.csv`; fields are fixed from the first write and later extra fields are ignored. |
| `loggers.make_default_logger(label, save_data=True, time_delta=1.0, asynchronous=False, print_fn=None, serialize_fn=base.to_numpy, steps_key='steps')` | Builds terminal plus optional CSV logging, filters `None`, optionally dispatches asynchronously, and throttles by time. |
| `observers.EnvLoopObserver` | Interface with `observe_first(env, timestep)`, `observe(env, timestep, action)`, and `get_metrics()`. |
| `observers.ActionNormObserver` | Adds action norm average/min/max metrics. |
| `observers.EnvInfoObserver` | Sums scalar values from environments exposing `get_info()`. Pairs naturally with `GymWrapper`. |
| `observers.MeasurementObserver` | Adds per-index observation distribution metrics for low-dimensional observations. |

Important optional dependency note: `acme.utils.loggers.base` imports `jax` to convert JAX arrays in `to_numpy`. In an environment with only the minimal `dm-acme` core dependencies, importing `acme.utils.loggers` can fail unless JAX is installed or the package version has been patched. Use `NoOpLogger` only after the logger module import succeeds, or provide a tiny custom object with `write(data)` and `close()` if you need to avoid Acme logger imports entirely.
