# Embodied API Contracts

This reference distills the Embodied core contracts used by DreamerV3. It is
self-contained: future agents should not need to reopen source files to wire a
custom environment, driver callback, replay buffer, or stream.

## Import surface

Typical imports are:

```python
import embodied
from embodied.core import selectors, streams
from embodied.envs import dummy
```

Important public objects for this sub-skill:

| Object | Purpose |
| --- | --- |
| `embodied.Env` | Base class/duck-type contract for environments. |
| `embodied.Agent` | Base class contract for policies, train/report methods, state save/load. |
| `embodied.Driver` | Steps one or more envs and calls callbacks with transitions. |
| `embodied.Replay` | Stores per-worker sequences and samples batches for training/report/eval. |
| `embodied.RandomAgent` | Safe policy smoke agent that samples action spaces except `reset`. |
| `embodied.core.streams.*` | Stateless, Prefetch, Consec, Zip, Map, and Mixer stream combinators. |
| `embodied.core.selectors.*` | Replay item selectors: FIFO, uniform, recency, prioritized, and mixtures. |
| `embodied.wrappers.*` | Environment wrappers for action scaling, dtype/space checks, resizing, limits, and crash restart. |

## Environment contract

An environment can subclass `embodied.Env` or implement the same interface:

```python
class MyEnv(embodied.Env):
  @property
  def obs_space(self):
    return {...}  # dict[str, elements.Space]

  @property
  def act_space(self):
    return {...}  # dict[str, elements.Space], must include 'reset'

  def step(self, action):
    return {...}  # dict[str, scalar/array values]

  def close(self):
    pass
```

### Observation keys

Every observation returned by `step()` must contain at least:

| Key | Type/shape convention | Meaning |
| --- | --- | --- |
| `reward` | `np.float32` scalar | Reward for the transition. Reset observations normally use `0.0`. |
| `is_first` | `bool` scalar | True on the first observation after a reset. |
| `is_last` | `bool` scalar | True on the observation that ends the episode or segment. |
| `is_terminal` | `bool` scalar | True when the environment ended terminally. Time-limit boundaries can set `is_last=True` and `is_terminal=False` when appropriate. |

Common additional keys are `image`, `vector`, tokens, proprioceptive values,
inventory features, or task-specific observations. Keys starting with `log/`
are special: the `Driver` strips them before calling the policy and then adds
them back to callback transitions. Use `log/` for metrics that should be saved
or logged but not consumed by the agent.

### Action keys

`act_space` must include:

| Key | Required | Meaning |
| --- | --- | --- |
| `reset` | yes | Boolean scalar. `True` asks the env to reset and return an `is_first` observation. The policy should not produce this key; the driver supplies it. |
| environment actions | usually | Discrete or continuous controls such as `action`, `act_disc`, or `act_cont`. |

Action and observation key sets should not overlap. `CheckSpaces` asserts this
up front and then checks every `step()` value against the declared space.

### Space contract

Embodied environments use `elements.Space(dtype, shape=(), low=None, high=None)`.
Use these conventions:

- Scalars use shape `()` and should be returned as NumPy scalars, Python scalars,
  or zero-dimensional arrays accepted by the space.
- Images are usually `np.uint8` with shape `(height, width, channels)`.
- Continuous actions are usually `np.float32` vectors. Finite bounds allow
  `NormalizeAction` to expose `[-1, 1]` to the agent.
- Discrete actions are usually `np.int32` scalar values with bounds matching the
  valid action ids.
- If the backend emits `float64` or platform integers, add `UnifyDtypes` before
  `CheckSpaces` during development.

### Reset semantics

A robust `step(action)` follows this pattern:

```python
def step(self, action):
  reset = bool(np.asarray(action['reset']).item())
  if reset or self._done:
    self._done = False
    self._step = 0
    return self._obs(reward=0.0, is_first=True, is_last=False,
                     is_terminal=False)
  # Apply normal action, increment counters, compute reward.
  self._done = ...
  return self._obs(reward=reward, is_first=False, is_last=self._done,
                   is_terminal=terminal)
```

The first observation is still a transition seen by the `Driver` callback. For a
length-10 dummy episode, one episode produces 11 callback transitions: the
initial reset observation plus 10 non-reset steps.

## Agent contract

`embodied.Agent` defines these methods:

| Method | Contract |
| --- | --- |
| `__init__(obs_space, act_space, config)` | Build an agent for the environment spaces and config. |
| `init_policy(batch_size)` | Return initial policy carry/state for `batch_size` parallel envs. |
| `policy(carry, obs, mode)` | Return `(carry, act, out)`. `obs` is batched by env, `act` is batched and must not include `reset`, `out` must not collide with `act` keys. |
| `init_train(batch_size)` | Return carry/state for training batches. |
| `train(carry, data)` | Return `(carry, out, metrics)` from replay batch data. |
| `init_report(batch_size)` | Return carry/state for reporting batches. |
| `report(carry, data)` | Return `(carry, metrics)`. |
| `stream(st)` | Optional stream transformation hook. |
| `save()` / `load(data)` | Serialize and restore agent state. |

`embodied.RandomAgent(obs_space, act_space)` is useful for contract smoke tests.
It samples every action space except `reset` and returns empty policy outputs.

## Driver contract

Construct a driver with one or more zero-argument environment factories:

```python
driver = embodied.Driver([make_env, make_env], parallel=False)
driver.reset(agent.init_policy)
driver.on_step(lambda tran, worker: replay.add(tran, worker=worker))
driver(agent.policy, steps=1000)       # run for at least 1000 env transitions
driver(agent.policy, episodes=10)      # run until 10 episode endings
driver(agent.policy, steps=100, episodes=1)  # continues until both goals met
```

### Driver state and reset

- On construction, `Driver` discovers `act_space` from the first env.
- `driver.reset(init_policy)` initializes all actions to zeros and sets
  `reset=True` for every env. If `init_policy` is provided, it is called as
  `init_policy(num_envs)` and the result becomes policy carry.
- After each env step, `Driver` calls the policy with batched observations.
- If any observation has `is_last=True`, the driver masks the policy action for
  that finished env to zeros on the terminal callback transition and schedules
  `reset=True` for the next env step.

### Policy inputs and outputs

The policy sees only non-log observations. For `N` envs:

- Every observation array has leading dimension `N`.
- The policy returns action arrays with leading dimension `N` and shapes matching
  the non-reset action spaces.
- The policy may return auxiliary `out` arrays. These are included in callback
  transitions but must not use the same keys as actions.

### Callback transition contents

Each callback receives one unbatched transition per worker:

```python
def callback(tran, worker, **driver_kwargs):
  ...
```

`tran` contains:

- Observation keys except that `log/` keys are restored after policy execution.
- Action keys returned by the policy. In the inspected implementation, the
  driver's internal reset scheduling key is not part of callback transitions
  unless user policy code incorrectly returns a `reset` action. Prefer
  `is_first` and `is_last` for episode-boundary logic in callbacks and replay.
- Policy output keys.
- `log/` observation keys, useful for episode metrics and diagnostics.

Use the `worker` argument as the replay worker id. Do not replace it with a
constant when collecting from multiple envs.

### Parallel mode

`Driver(make_env_fns, parallel=True)` starts one process per env factory and
communicates over pipes. Use it only when factories are picklable, imports are
available in child processes, and the environment can be created independently
per worker. If a worker raises an exception, the driver terminates workers and
re-raises a `RuntimeError` containing the child-side error.

For contract debugging, prefer `parallel=False`; switch to parallel only after
single-process stepping passes.

## Replay contract

Construct replay with:

```python
replay = embodied.Replay(
    length=16, capacity=10000, directory=None, chunksize=1024,
    online=False, selector=None, save_wait=False, name='train', seed=0)
```

| Argument | Meaning |
| --- | --- |
| `length` | Number of consecutive time steps returned per sampled sequence. |
| `capacity` | Maximum number of sampleable sequence start items, not raw steps. `None` means unbounded except memory/disk. |
| `directory` | Optional directory for chunk `.npz` persistence. Without it, replay is in-memory only. |
| `chunksize` | Number of raw steps per chunk before linking a successor chunk. |
| `online` | If true, every `length` steps per worker can be queued for immediate train sampling. |
| `selector` | Optional selector; defaults to uniform sampling. |
| `save_wait` | If true, wait for asynchronous chunk save futures. |
| `seed` | Selector/random seed for reproducible sampling. |

### Adding transitions

```python
replay.add(tran, worker=worker_id)
```

- `tran` is copied to NumPy arrays and keys starting with `log/` are dropped.
- Replay adds a `stepid` field. It encodes chunk uuid plus index and is required
  for priority and sequence updates.
- Each `worker` has an independent stream and current chunk. Sequence starts are
  inserted only after that worker has at least `length` steps.

### Sampling batches

For the inspected API, use:

```python
batch = replay.sample(batch=8, mode='train')
```

- `mode` must be `train`, `report`, or `eval`.
- Sampling blocks until at least one item is available.
- Returned arrays have shape `(batch, length, *value_shape)`.
- If `is_first` exists, replay can set `is_first[:, 0] = True` for sampled
  batches and can mark `is_last` before a following `is_first` to avoid silently
  continuing across abandoned episode boundaries.
- `stats()` reports item/chunk counts and then resets insert/sample/update
  counters.

Some older snippets or tests may refer to a `dataset()` wrapper around replay.
When working with this version, verify whether that wrapper exists in the local
package; the direct public method evidenced here is `sample(batch, mode)`.

### Updating priorities or stored sequence values

```python
data = {
    'stepid': batch['stepid'],             # shape (B, T, 20)
    'priority': priority_array,            # optional shape (B, T)
    'some_key': replacement_values,        # optional sequence values
}
replay.update(data)
```

- `priority` is forwarded to selectors that implement `prioritize()`.
- Extra keys update the stored sequence values at the corresponding step ids.
- Updates can be ignored for removed chunks/items, so code should tolerate stale
  update attempts after capacity eviction.

## Stream contract

`embodied.core.base.Stream` is an iterator with save/load:

```python
stream = iter(stream)
batch = next(stream)
state = stream.save()
stream.load(state)
```

Available stream helpers:

| Stream | Contract |
| --- | --- |
| `Stateless(nextfn, *args, **kwargs)` | Calls a stateless function each `next()`. `save()` returns `None`. |
| `Prefetch(source, transform=None, amount=1)` | Runs a background thread, prefetches transformed items, and can save/load the source state. Start it by calling `iter(stream)` once. |
| `Consec(source, length, consec, prefix=0, strict=True, contiguous=False)` | Splits a larger sampled batch into consecutive windows. Requires source time dimension to fit `consec * length + prefix`; adds `consec` index. |
| `Zip(sources)` | Iterates multiple sources and concatenates matching tree leaves along the first dimension. |
| `Map(source, fn, *args, **kwargs)` | Applies a function to each source item and delegates save/load to the source iterator. |
| `Mixer(sources, weights, seed=0)` | Intended to randomly mix named sources by weight; smoke-test before relying on it because stream implementations can be version-sensitive. |

Use streams after replay sampling when you need prefetching, transformation,
consecutive minibatches, or combined train/report sources. Keep stream state in
checkpoints only after `save()`/`load()` has been exercised in a small smoke.
