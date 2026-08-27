# Advanced environment patterns

This reference covers environment-side contracts for vectorization, multi-actor environments, and remote environment execution. Use the runner workflow sub-skill for complete `Runner(...)` training/evaluation recipes.

## Vectorized environments

A vectorized Tensorforce environment represents multiple independent instances inside one environment object.

Contract:

- Override `is_vectorizable(self)` and return `True`.
- `reset(num_parallel=N)` initializes `N` internal instances and returns `(parallel_indices, states)`.
- `execute(actions)` accepts a batched action array/dict for the currently active parallel indices and returns `(parallel_indices, states, terminal, reward)`.
- `parallel_indices` identify the still-active instances. Drop indices whose episodes terminated.
- `terminal` and `reward` are vectors aligned with the pre-execute active parallel set. `states` are aligned with the returned still-active `parallel_indices`.
- For non-vectorized calls (`reset()` with no `num_parallel`), return ordinary unbatched values.

Skeleton:

```python
import numpy as np
from tensorforce import Environment

class VectorizedCounter(Environment):
    def __init__(self):
        super().__init__()

    def states(self):
        return dict(type='int', shape=(), num_values=11)

    def actions(self):
        return dict(type='int', shape=(), num_values=3)

    def is_vectorizable(self):
        return True

    def reset(self, num_parallel=None):
        self._is_parallel = (num_parallel is not None)
        self._parallel = np.arange(num_parallel if self._is_parallel else 1)
        self._states = np.zeros(shape=self._parallel.shape, dtype=np.int32)
        if self._is_parallel:
            return self._parallel.copy(), self._states.copy()
        return int(self._states[0])

    def execute(self, actions):
        if not self._is_parallel:
            actions = np.expand_dims(actions, axis=0)
        self._states = np.clip(self._states + (actions - 1), 0, 10)
        terminal = self._states >= 10
        reward = self._states.astype(np.float32) / 10.0
        if self._is_parallel:
            self._parallel = self._parallel[~terminal]
            self._states = self._states[~terminal]
            return self._parallel.copy(), self._states.copy(), terminal, reward
        return int(self._states[0]), bool(terminal.item()), float(reward.item())
```

When wrapped by `Environment.create(..., max_episode_timesteps=N)`, a vectorized environment that reaches the wrapper time limit can receive abort terminals (`2`) for still-running instances. The wrapper may return an empty `parallel` vector and `states=None` when the time limit aborts all remaining instances, so interaction loops must handle that case.

## Multi-actor environments

A multi-actor environment represents multiple actors sharing one world state. It is not the same as vectorization: actors may interact with each other and may terminate independently.

Contract:

- Override `num_actors(self)` to return an integer greater than 1.
- Do not also mark the same environment vectorizable; Tensorforce's wrapper rejects simultaneous vectorizable + multi-actor mode.
- `reset()` returns `(parallel_indices, states)`, where each index is an actor id and `states` is the actor-perspective state batch.
- `execute(actions)` receives one action per active actor and returns `(parallel_indices, states, terminal, reward)`.
- Update `parallel_indices` to keep only actors still active after the step.

Skeleton:

```python
import numpy as np
from tensorforce import Environment

class TwoActorLine(Environment):
    def __init__(self):
        super().__init__()

    def states(self):
        return dict(type='int', shape=(), num_values=11)

    def actions(self):
        return dict(type='int', shape=(), num_values=3)

    def num_actors(self):
        return 2

    def reset(self):
        self._parallel = np.arange(2)
        self._position = 5
        states = np.asarray([self._position, 10 - self._position], dtype=np.int32)
        return self._parallel.copy(), states

    def execute(self, actions):
        active = self._parallel.copy()
        actions = np.asarray(actions).reshape(-1)
        assert actions.shape[0] == active.shape[0]

        if active.shape[0] == 2:
            delta = int(actions[0] - 1) - int(actions[1] - 1)
            self._position = int(np.clip(self._position + delta, 0, 10))
            states = np.asarray([self._position, 10 - self._position], dtype=np.int32)
            terminal = np.asarray([False, self._position in (0, 10)], dtype=bool)
        else:
            delta = int(actions[0] - 1)
            self._position = int(np.clip(self._position + delta, 0, 10))
            states = np.asarray([self._position], dtype=np.int32)
            terminal = np.asarray([self._position in (0, 10)], dtype=bool)

        reward = (states.astype(np.float32) - 5.0) / 5.0
        self._parallel = active[~terminal]
        return self._parallel.copy(), states[~terminal], terminal, reward
```

## Local parallel execution boundaries

There are three common local patterns:

1. **Independent local environments**: `num_parallel=N` with a normal environment spec lets the runner coordinate N environment instances. Use when environment steps are cheap and batching agent calls is beneficial.
2. **One vectorized environment**: `num_parallel=N` with `environment.is_vectorizable() == True` uses one vectorized environment object. Use when the simulator can step many instances more efficiently than Python can step N objects.
3. **Multiprocessing remote environments**: `remote='multiprocessing'` starts environment work in child processes. Use when environment steps are slow enough to justify process communication overhead.

Environment-side multiprocessing factory form:

```python
env = Environment.create(
    environment=MyEnvironment,
    max_episode_timesteps=100,
    remote='multiprocessing',
    blocking=False,
)
```

Multiprocessing caveats:

- The environment spec/class and constructor kwargs must be importable/picklable by the child process.
- Close the wrapper to join the child process.
- Do not use `host` or `port`; those are socket-only.
- `blocking` is valid only for multiprocessing and socket-client modes.

## Socket client/server boundaries

Tensorforce can separate environment processes over a socket. The environment side and agent side have different responsibilities.

**Server side owns the environment spec** and blocks inside a communication loop until the client closes:

```python
Environment.create(
    environment=MyEnvironment,
    max_episode_timesteps=100,
    remote='socket-server',
    port=65432,
)
```

**Client side owns host/port and must not pass environment/max-timestep kwargs**:

```python
env = Environment.create(
    remote='socket-client',
    host='127.0.0.1',
    port=65432,
    blocking=False,
)
```

Socket caveats:

- Start the server before the client. The client retries briefly, then raises a connection error.
- The server binds to the requested port; only one server can own a port.
- Do not pass `environment`, `max_episode_timesteps`, or adapter kwargs to a socket client.
- Do not pass `host` except to a socket client.
- Socket mode can hang if the server is left waiting or a client dies without close; keep smoke tests bounded and close explicitly.

## Remote and runner interaction

For full training workflows, prefer `Runner(...)` to coordinate multiple environments. If an agent and environment are created separately, the caller must ensure the agent's `parallel_interactions` matches the number of parallel environment interactions. Keep those agent-side details in the agent/runner sub-skills; this sub-skill only defines what environment methods must return.

## CARLA/manual simulators

Some simulators expose their own event loop and manual training helpers. In particular, the CARLA adapter surface is external-service-based and notes that the standard Tensorforce runner is not compatible. Treat those as manual/direct environment workflows unless a user-provided bounded check proves otherwise.
