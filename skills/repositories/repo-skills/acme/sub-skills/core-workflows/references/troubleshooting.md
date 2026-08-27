# Core Troubleshooting

Use this guide for failures before a backend-specific Acme agent is involved. Most core problems are environment/spec mismatches, wrapper ordering issues, loop bound misuse, logging/import surprises, or optional dependency confusion.

## `EnvironmentLoop.run()` Raises About Bounds

Symptom:

```text
ValueError: Either "num_episodes" or "num_steps" should be None.
```

Cause: `EnvironmentLoop.run(num_episodes=..., num_steps=...)` accepts at most one finite bound.

Fix:

- Use `loop.run(num_episodes=N)` to run complete episodes.
- Use `loop.run(num_steps=N)` to run at least `N` steps; the last episode is still completed, so the return value may be greater than `N`.
- Use `loop.run()` only for an unbounded worker loop that should run until interrupted.

## Actor Action Does Not Match `action_spec()`

Symptoms:

- The environment rejects an action shape, dtype, nested structure, or range.
- `spec.validate(action)` fails.
- A Gym environment works with sampled Gym actions but fails through Acme.

Checks:

```python
environment_spec = specs.make_environment_spec(environment)
print(environment_spec.actions)
action = actor.select_action(environment.reset().observation)
print(action, type(action), getattr(action, 'shape', None), getattr(action, 'dtype', None))
```

Fixes:

- Return the same nested structure as `environment_spec.actions`.
- For `specs.DiscreteArray`, return a scalar integer-like value with the declared dtype.
- For `specs.BoundedArray`, return an array with the declared shape/dtype and values within min/max.
- Add `SinglePrecisionWrapper` if the environment emits float64/int64 values but the agent assumes float32/int32.
- Add `CanonicalSpecWrapper(clip=True)` only when the actor intentionally emits continuous actions in `[-1, 1]` and the wrapped environment has bounded continuous actions.

## Environment Is Gym-Like, Not `dm_env`-Compatible

Symptoms:

- Environment has `observation_space`/`action_space` instead of `observation_spec()`/`action_spec()`.
- `reset()` returns a raw observation instead of a `dm_env.TimeStep`.
- `step()` returns `(observation, reward, done, info)`.

Fix:

- Use `acme.wrappers.GymWrapper(raw_gym_env)` when the installed Gym API matches Acme's wrapper expectations.
- For newer Gym/Gymnasium-style APIs, adapt `reset()` and `step()` to the older Gym tuple shape before wrapping, or implement `dm_env.Environment` directly.
- Verify `specs.make_environment_spec(wrapped_env)` before wiring an actor.
- Use `EnvInfoObserver` only if the wrapper exposes `get_info()` and the info values you need are scalar.

## Reward or Discount Shape Breaks Return Accumulation

Symptoms:

- Episode return accumulation fails inside `EnvironmentLoop.run_episode()`.
- `episode_return` has an unexpected nested structure.

Cause: `EnvironmentLoop` initializes zeros from `environment.reward_spec()` and uses tree-structured in-place addition with every `timestep.reward`.

Fix:

- Ensure `reward_spec()` matches the reward emitted by every non-reset step.
- Ensure nested rewards have stable keys/shapes across the episode.
- Ensure reward dtype supports addition into `np.zeros(spec.shape, spec.dtype)`.
- If using vector rewards, expect vector `episode_return` metrics instead of scalar returns.

## Logger Import Fails in a Core-Only Install

Symptoms:

```text
ModuleNotFoundError: No module named 'jax'
```

or a similar import failure while importing `acme.utils.loggers` or constructing the default `EnvironmentLoop` logger.

Cause: In this Acme version, `acme.utils.loggers.base` imports `jax` so `to_numpy()` can convert JAX arrays. The package metadata keeps JAX in the optional `jax` extra, so minimal core installs can still hit this import path when logging utilities are imported.

Fix options:

- Install the matching optional JAX extra when the task actually needs Acme loggers or JAX agents.
- Pass a small custom logger object with `write(data)` and `close()` to `EnvironmentLoop` to avoid constructing Acme's default logger while doing core environment debugging.
- Use the bundled `scripts/check_core_imports.py --json` to see whether the failure is in top-level `acme`, logger imports, or optional backend imports.

Do not route a pure core environment/spec issue to the JAX sub-skill solely because this logger import mentions JAX; first decide whether the user truly needs backend execution.

## Default Logger Does Not Print Every Episode

Symptoms:

- `EnvironmentLoop.run()` completes but terminal/CSV output appears sparse.
- Fast episodes are missing from the log.

Cause: `loggers.make_default_logger(..., time_delta=1.0)` throttles writes by default. `TerminalLogger` itself defaults to `time_delta=0.0`, but the default logger wraps dispatch with a `TimeFilter`.

Fix:

```python
logger = loggers.make_default_logger(
    'environment_loop', save_data=False, time_delta=0.0, print_fn=print)
loop = EnvironmentLoop(environment, actor, logger=logger)
```

For CSV logging, remember that `CSVLogger` chooses columns from the first write and ignores extra fields added later.

## Optional Launchpad, Reverb, TensorFlow, or JAX Imports Fail

Symptoms:

- Import errors for `launchpad`, `reverb`, `tensorflow`, `sonnet`, `trfl`, `jax`, `haiku`, `flax`, `optax`, or `rlax`.
- A user installed only `dm-acme` and expects all agents/examples to run.

Cause: Core `dm-acme` is minimal. Optional extras are split by backend: JAX agents use the JAX stack plus TensorFlow/Reverb/Launchpad packages; TensorFlow/Sonnet agents use Sonnet/TRFL plus TensorFlow/Reverb/Launchpad packages; environment examples may require Gym, Atari, dm-control, bsuite, pygame, or RLDS.

Fix:

- For core loop/spec work, avoid importing backend packages and keep examples to `dm_env`, `acme.core`, and `acme.specs` where possible.
- For JAX experiments or agent builders, route to `jax-agents` and verify JAX stack versions.
- For TF/Sonnet agents or Launchpad TF examples, route to `tf-agents` and verify TF/Reverb/Launchpad compatibility.
- For replay buffers or dataset pipelines, route to `replay-and-data`.
- Report optional dependency absence as expected when the workflow does not require that backend.

## Wrapper Ordering Produces Strange Specs

Symptoms:

- Public action spec changes unexpectedly.
- Action range appears to be `[-1, 1]` but the environment expects another range.
- Observations are stacked/concatenated with unexpected shapes.

Fix:

- Put API adapters first: wrap raw Gym with `GymWrapper` before `dm_env` wrappers.
- Apply dtype normalization before agent code that assumes single precision.
- Apply `CanonicalSpecWrapper` only once and only when the actor is designed for canonical continuous actions.
- Recompute and print `specs.make_environment_spec(environment)` after each wrapper while debugging.
- Prefer explicit wrapper lists with `wrappers.wrap_all` so order is auditable.

## `OpenSpielEnvironmentLoop` Fails

Symptoms:

- `ModuleNotFoundError: No module named 'pyspiel'`.
- `ValueError: Currently only supports sequential games.`

Cause: OpenSpiel support is optional and uses a separate multi-agent loop. The loop expects `OpenSpielWrapper`, a sequence of actors, and turn-based games.

Fix:

- Use ordinary `EnvironmentLoop` for single-agent `dm_env` environments.
- Install/verify OpenSpiel only when the task is specifically about OpenSpiel.
- Avoid simultaneous-move games with this loop unless implementing additional support.

## Observer Metrics Are Missing or Explode in Size

Symptoms:

- `EnvInfoObserver` adds no metrics.
- `MeasurementObserver` creates many metric keys.
- `ActionNormObserver` emits `nan` for empty episodes.

Fix:

- `EnvInfoObserver` requires the environment to expose `get_info()` and only accumulates scalar values.
- `MeasurementObserver` is intended for low-dimensional observations; do not attach it to image observations or large nested structures.
- For zero-step episodes, action-based observers may have no action values; use a custom observer that handles empty episodes if this is expected.
- Check observer key collisions: observer metrics are merged into the episode result dictionary and can overwrite earlier keys if names collide.

## Clean Debugging Sequence

When several failures happen at once, reset to this order:

1. Run `scripts/check_core_imports.py --json` and separate core import failures from optional dependency absence.
2. Build the environment only; print all four specs.
3. Reset and step with `environment_spec.actions.generate_value()`.
4. Add wrappers one by one and reprint specs.
5. Add a minimal spec-generated-action actor.
6. Run `EnvironmentLoop(..., logger=custom_print_logger).run(num_episodes=1)`.
7. Add Acme loggers, counters, and observers.
8. Route backend-specific learner, replay, or distributed issues to the appropriate sub-skill.
