# Environment troubleshooting

Use this checklist to diagnose Tensorforce environment failures without depending on a source checkout.

## Factory argument errors

### Unknown environment string

Symptom: `Environment.create(...)` reports an invalid value for `environment`.

Likely causes:

- The string is not a Tensorforce registry key.
- It is not an importable Python module/class path.
- It is not a Gym level recognized by the installed Gym version.

Fixes:

- Use an explicit registry key and required arguments, for example `environment='gym', level='CartPole-v1'`.
- Import/register custom Gym environments before calling `Environment.create(...)`, or use the Gym adapter's `import_modules` argument.
- For a custom Tensorforce class, pass the class object or an importable module path resolving to the class.

### `blocking`, `host`, or `port` rejected

Rules enforced by the factory:

- `blocking` is valid only with `remote='multiprocessing'` or `remote='socket-client'`.
- `host` is valid only with `remote='socket-client'`.
- `port` is valid only with `remote='socket-client'` or `remote='socket-server'`.
- `remote='socket-client'` must not receive `environment`, `max_episode_timesteps`, or extra environment kwargs.
- `remote='socket-server'` owns the environment spec and blocks in a server loop.

If a socket client says it cannot connect, start the socket server first, check that the port is free, and keep a bounded timeout around the workflow.

## Custom environment output errors

### Invalid state component

Symptom: `Environment.reset` or `Environment.execute` reports an invalid component for state.

Rules:

- If `states()` returns one unnamed spec such as `dict(type='float', shape=(4,))`, return a bare array/scalar. If returning a dict, the main state key must be `state`; additional action masks may end in `_mask`.
- If `states()` returns a dict of named specs, returned state dict keys must match those names. Extra keys are allowed only for masks ending in `_mask`.
- For action masks, use `action_mask` for a single/default action, or `<action_name>_mask` for named discrete actions.

### Invalid shape or dtype

Symptom: Tensorforce reports invalid shape/type for a state, action, terminal, or reward.

Fixes:

- Return NumPy arrays or Python scalars matching the declared `shape` exactly.
- Use scalar `shape=()` for scalar actions/states.
- Integer discrete specs should include `num_values` in Tensorforce 0.6.x.
- Keep float states/actions finite unless the adapter explicitly handles infinities.
- For multi-component specs, make every component independently match its spec.

### Invalid terminal value

Valid single-environment terminal values are `False`, `True`, `0`, `1`, or `2`.

- `0`/`False`: continue.
- `1`/`True`: true terminal state.
- `2`: abort terminal, usually time-limit truncation.

For vectorized environments, return a bool vector or an int vector with values in `{0, 1, 2}`. Rewards must be numeric scalars or numeric vectors aligned with the active parallel instances.

### `execute()` called before `reset()`

The Tensorforce wrapper tracks episode state. Always call `reset()` before the first `execute()` of an episode and after any terminal/abort terminal.

## Max-timestep and abort-terminal issues

If a task has a training horizon but no true natural terminal at that horizon, do **not** make the raw environment return `True` at the time limit. Instead:

```python
env = Environment.create(environment=MyEnvironment, max_episode_timesteps=200)
```

The wrapper converts a still-running episode at timestep 200 into `terminal=2`. That preserves the distinction between a task failure/success terminal and a time-limit abort.

If `max_episode_timesteps` is missing, some agent/runner configurations may have insufficient horizon information. Prefer to set it explicitly unless the environment has a reliable natural fixed limit.

## Reward shaping failures

Reward shaping receives previous states, actions, terminal, raw reward, and next states.

Common mistakes:

- Returning a non-numeric reward.
- Returning `(terminal, reward)` instead of `(reward, terminal)`.
- Assuming string shaping sees variables other than `states`, `actions`, `terminal`, `reward`, `next_states`, `math`, `np`, and `random`.
- Using untrusted user text as a shaping expression. The string form is evaluated as code; use only trusted configuration.
- Expecting the shaping function to see wrapper-generated time-limit `terminal=2`. The wrapper applies the max-timestep conversion after reward shaping, so shaping sees the raw environment terminal for that step.

## Gym adapter issues

### New Gym/Gymnasium API mismatch

Tensorforce 0.6.x expects older Gym behavior:

- `reset()` returns `observation` only.
- `step(action)` returns `(observation, reward, terminal, info)`.

Newer Gym/Gymnasium may return `(observation, info)` from reset and `(observation, reward, terminated, truncated, info)` from step. Use a compatible Gym release, a compatibility wrapper that merges `terminated/truncated` into Tensorforce terminal semantics, or a custom Tensorforce `Environment` subclass.

### Infinite Box bounds

If Gym Box observations/actions have infinite bounds, Tensorforce may need explicit `min_value` and `max_value` clipping values:

```python
env = Environment.create(
    environment='gym', level='SomeEnv-v0', min_value=-10.0, max_value=10.0
)
```

### Custom Gym registration

If the Gym id is registered by importing a package/module, either import it before `Environment.create(...)` or pass `import_modules='your_registration_module'` to the Gym adapter.

## Optional simulator adapters

If ALE, Retro, ViZDoom, OpenSim, PLE, or CARLA fails to import or initialize:

- Confirm the optional Python package is installed in the active runtime.
- Confirm required game/simulator assets, ROMs, config files, or server processes exist.
- For CARLA, confirm the simulator server is running and compatible with the installed Python bindings.
- For headless pygame/PLE workflows, confirm SDL can use a dummy/headless video driver.
- For ViZDoom/ALE/Retro, confirm required system libraries and assets are installed.

These failures do not prove the core Tensorforce environment API is broken; they usually indicate optional dependency or external-service setup.

## Multiprocessing and socket hangs

Checklist:

- Make the environment class importable/picklable for multiprocessing.
- Avoid passing live simulator handles, open files, or sockets into a multiprocessing environment spec unless they are created inside the child.
- Start socket servers before socket clients.
- Use one free port per socket server.
- Close environments in `finally` blocks so child processes and sockets are released.
- Keep remote smoke tests bounded. A socket server call intentionally blocks until the client closes.

## Vectorized and multi-actor mistakes

Vectorized environments:

- `reset(num_parallel=N)` must return `(parallel_indices, states)`.
- `execute(actions)` must return `(parallel_indices, states, terminal, reward)`.
- Returned `parallel_indices` and `states` represent still-active instances after the step.
- `terminal`/`reward` vectors represent the active instances before the step.

Multi-actor environments:

- `num_actors()` returns the initial number of actors.
- Do not also return `True` from `is_vectorizable()`.
- Actor indices should identify the currently active actor perspectives.
- Returned actions/states/terminal/reward arrays must stay aligned with active actor indices.

## Dependency resolver conflict

Tensorforce 0.6.x has old dependency metadata around NumPy/TensorFlow. In modern pip resolution, a direct install can conflict because Tensorforce pins an older NumPy line while TensorFlow 2.12 requires a newer NumPy range. A practical workaround is to use a clean Python 3.8-style environment, install a TensorFlow-compatible NumPy version below 1.25, install Tensorforce without forcing broad optional extras, and run a live import/API smoke. Record any local metadata workaround separately; do not patch user source unless explicitly asked.
