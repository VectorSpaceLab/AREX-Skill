# Parallel Authoring

Parallel environments step all live agents at once. Use `ParallelEnv` when every active agent chooses an action for the same environment tick.

## Public Factories

Expose these entry points from the versioned module:

- `parallel_env(...)`: returns the bare `ParallelEnv` implementation.
- `raw_env(...)`: converts the parallel environment to an AEC environment with `parallel_to_aec(parallel_env(...))`.
- `env(...)`: wraps `raw_env(...)` for normal users with AEC utility wrappers such as `AssertOutOfBoundsWrapper` and `OrderEnforcingWrapper`.

Set `metadata["is_parallelizable"] = True` only when the environment can safely round-trip between AEC and Parallel semantics, meaning state changes happen at cycle boundaries rather than after a single agent's partial turn.

## Required Reset Contract

`reset(seed=None, options=None)` returns exactly `(observations, infos)`.

- `observations`: dictionary keyed by every live agent after reset.
- `infos`: dictionary keyed by the same live agents, even when each value is `{}`.
- `self.agents`: live agents for the current episode, normally a copy of `possible_agents`.
- Internal state: positions, counters, scores, RNG state, and any render state used later.

If the environment has stochastic reset state, seed the environment RNG inside `reset(seed=...)` and draw from that RNG only.

## Required Step Contract

`step(actions)` receives a dictionary of actions keyed by the current live agents and returns exactly:

```text
observations, rewards, terminations, truncations, infos
```

Each returned value is a dictionary keyed by relevant agents:

- `observations`: next observations for agents that receive one from this transition.
- `rewards`: numeric rewards assigned by this transition.
- `terminations`: true for agents that reached an environment terminal condition.
- `truncations`: true for agents stopped by a time limit or external cutoff.
- `infos`: per-agent metadata; include `{}` when there is no extra information.

When the episode ends for all agents, build the returned dictionaries first, then set `self.agents = []`. This preserves the final transition while making the next loop stop cleanly.

## Agent Lifecycle

- `possible_agents` is the complete roster and should not change after initialization.
- `agents` is the live roster for the current episode and may shrink after terminal or truncation events.
- Returned dictionary keys must match the lifecycle the environment reports. Many compliance failures come from returning rewards or infos for agents that are no longer live too early, or omitting a live agent before it receives its final transition.
- If a user passes an empty action dictionary after the episode is over, it is safe to return five empty dictionaries and leave `agents` empty.

## Spaces And Observations

- Implement `observation_space(agent)` and `action_space(agent)` rather than relying on deprecated `observation_spaces` and `action_spaces` attributes.
- Static spaces can use `@functools.lru_cache(maxsize=None)` or stable dictionaries created in `__init__`.
- Observation values must match the declared space structure, shapes, dtypes, and bounds.
- For dictionary observations with action masks, declare a `spaces.Dict` containing both the actual observation and the mask.

## Rendering And State

- Include `metadata["render_modes"]` when render modes are supported.
- `render_mode="human"` should display or print and may return `None`.
- `render_mode="ansi"` should return a string when supported directly; if the AEC `env()` wrapper captures stdout, construct the raw environment with human-style printing and wrap it with `CaptureStdoutWrapper`.
- `state()` is optional, but if implemented it should return a global view useful for centralized training.
- `close()` should release windows, subprocesses, files, or other resources; if there are none, a no-op is fine.

## Versioned Layout

A minimal custom package usually separates logic from version exports:

```text
custom_package/
  env/custom_environment.py
  custom_environment_v0.py
```

The environment logic lives in the `env/` module. The versioned module imports and exposes `env`, `raw_env`, and optionally `parallel_env`. This lets future versions change behavior without breaking imports for older versions.

## Parallel Review Checklist

- `parallel_env()` constructs a fresh `ParallelEnv` instance.
- `raw_env()` converts with `parallel_to_aec` when an AEC API is needed.
- `env()` applies AEC wrappers around `raw_env()`, not directly around a `ParallelEnv`.
- `reset()` returns `(observations, infos)` and initializes `self.agents`.
- `step()` returns five dictionaries and updates `self.agents` only after preparing the final transition.
- Action and observation spaces are stable and match emitted data.
- Time limits use `truncations`; game-ending conditions use `terminations`.
- Randomness is reproducible through `reset(seed=...)`.
