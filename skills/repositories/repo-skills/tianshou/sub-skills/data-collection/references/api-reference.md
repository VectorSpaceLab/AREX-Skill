# Data Collection API Reference

This reference summarizes Tianshou 2.0.1 data-layer contracts for future coding agents. It is self-contained; do not rely on the source checkout being present.

## Public Imports

Use these stable public imports first:

```python
from tianshou.data import (
    AsyncCollector,
    Batch,
    CachedReplayBuffer,
    Collector,
    CollectStats,
    CollectStatsBase,
    HERReplayBuffer,
    HERVectorReplayBuffer,
    InfoStats,
    PrioritizedReplayBuffer,
    PrioritizedVectorReplayBuffer,
    ReplayBuffer,
    ReplayBufferManager,
    SequenceSummaryStats,
    TimingStats,
    VectorReplayBuffer,
    to_numpy,
    to_torch,
    to_torch_as,
)
```

Protocols used in type hints live in `tianshou.data.types`, including `ObsBatchProtocol`, `RolloutBatchProtocol`, `ActBatchProtocol`, `ActStateBatchProtocol`, `DistBatchProtocol`, `BatchWithReturnsProtocol`, `BatchWithAdvantagesProtocol`, and `PrioBatchProtocol`.

## Batch Contract

`Batch` is Tianshou's flexible data carrier: dictionary-like keys plus attribute access, recursive nesting, first-dimension slicing, and NumPy/Torch conversion.

Key behavior:

- Construction accepts `Batch(dict_or_batch_or_sequence=None, copy=False, **kwargs)`; dictionaries become nested `Batch` objects and lists of dictionaries are stacked.
- Keys must be strings; use `batch.obs` or `batch["obs"]` for field access.
- Integer, slice, list, and NumPy-array indexing slice every non-empty field and nested `Batch` recursively.
- `len(batch)` is the minimum leading length across non-empty fields; scalar-only fields can raise `TypeError` because they have no batch dimension.
- `batch.shape` is derived from contained values and may be conservative when keys have different shapes.
- `Batch.cat([...])` concatenates along the existing leading dimension and requires compatible structure.
- `Batch.stack([...], axis=0)` adds a dimension; partial keys are only supported with `axis=0`.
- `batch.split(size, shuffle=True, merge_last=False)` yields mini-batches; `size=-1` returns the whole batch.
- `batch.to_numpy()` and `batch.to_torch(dtype=None, device="cpu")` return converted copies; underscored variants mutate in place.
- `batch.isnull()`, `batch.hasnull()`, and `batch.dropnull()` support validation and cleanup of missing entries introduced by partial assignment or hooks.

Avoid storing lists of tensors with heterogeneous shapes as one field. If data is ragged, use object arrays intentionally and validate downstream code can handle them.

## Batch Protocols

Protocols document expected fields while runtime objects remain `Batch` instances:

- `ObsBatchProtocol`: `obs`, `info`; input to policies.
- `RolloutBatchProtocol`: `obs`, `info`, `obs_next`, `act`, `rew`, `terminated`, `truncated`; replay/collector transition data.
- `BatchWithReturnsProtocol`: rollout fields plus `returns`.
- `BatchWithAdvantagesProtocol`: rollout returns plus `adv` and `v_s`.
- `ActBatchProtocol`: `act`; minimal policy output.
- `ActStateBatchProtocol`: `act`, `state`; recurrent policy output.
- `DistBatchProtocol`: model output plus `dist`; stochastic policy output.
- `PrioBatchProtocol`: rollout fields plus `weight`; sampled prioritized replay batch.

When an API says it accepts a protocol, create a `Batch` with those fields and cast only for static typing if needed.

## ReplayBuffer Contract

Live signature:

```python
ReplayBuffer(
    size,
    stack_num=1,
    ignore_obs_next=False,
    save_only_last_obs=False,
    sample_avail=False,
    random_seed=42,
    **kwargs,
)
```

Core semantics:

- Fixed-size circular queue storing transitions in one underlying `Batch`.
- `add(batch, buffer_ids=None)` requires at least `obs`, `act`, `rew`, `terminated`, and `truncated`; it computes `done = terminated or truncated` internally.
- `add` returns `(insertion_index, episode_return, episode_length, episode_start_index)` as arrays; unfinished episodes return zero return/length.
- Reserved transition keys are `obs`, `act`, `rew`, `terminated`, `truncated`, `done`, `obs_next`, `info`, and `policy`.
- `sample(batch_size)` returns `(sampled_batch, indices)`; `batch_size=0` returns all currently available data, `None` samples `len(buffer)` items, and negative sizes return an empty sample.
- `buffer[index]` retrieves a `Batch`; `buffer[:]` means all available transitions in chronological availability order, not necessarily raw storage order.
- `prev(index)` and `next(index)` move along episode chronology while respecting `done` and sub-buffer edges.
- `get_buffer_indices(start, stop)` returns episode/slice indices, including edge-crossing circular intervals, but rejects intervals that cross vector sub-buffer boundaries.
- `get(index, key, default_value=None, stack_num=None)` retrieves frame-stacked values for keys such as `obs`.
- `hasnull()`, `isnull()`, and `dropnull()` delegate to the available sampled batch.
- `save_hdf5(path, compression=None)` and `load_hdf5(path, device=None)` persist and restore buffers.

## Buffer Variants

- `VectorReplayBuffer(total_size, buffer_num, **kwargs)`: manages one sub-buffer per environment. Use it with vectorized collection.
- `ReplayBufferManager(buffer_list)`: contiguous manager for same-type, same-options child buffers; normally use `VectorReplayBuffer` instead.
- `PrioritizedReplayBuffer(size, alpha, beta, weight_norm=True, **kwargs)`: prioritized experience replay; sampled batches include `weight`; call `update_weight(indices, new_weight)` after computing TD errors; `set_beta(beta)` updates importance-sampling strength.
- `PrioritizedVectorReplayBuffer(total_size, buffer_num, alpha, beta, **kwargs)`: vectorized prioritized replay.
- `CachedReplayBuffer(main_buffer, cached_buffer_num, max_episode_length)`: stores unfinished episodes in cache buffers and moves completed episodes to `main_buffer`.
- `HERReplayBuffer(size, compute_reward_fn, horizon, future_k=8.0, **kwargs)`: goal-conditioned hindsight replay with observation keys `observation`, `achieved_goal`, and `desired_goal`; `compute_reward_fn(achieved_goal, desired_goal)` must return shape `(batch_size,)` or compatible rewards.
- `HERVectorReplayBuffer(total_size, buffer_num, compute_reward_fn, horizon, future_k=8.0, **kwargs)`: vectorized HER replay.

## Collector Contract

Live signature:

```python
Collector(
    policy,
    env,
    buffer=None,
    exploration_noise=False,
    on_episode_done_hook=None,
    on_step_hook=None,
    raise_on_nan_in_buffer=False,
    collect_stats_class=CollectStats,
)
```

Important behavior:

- `env` may be a Gymnasium env or Tianshou vector env; a single Gymnasium env is wrapped in `DummyVectorEnv`.
- If `buffer=None`, the collector creates a `VectorReplayBuffer(DEFAULT_BUFFER_MAXSIZE * env_num, env_num)`.
- A plain `ReplayBuffer` is valid only for one environment; multiple environments need a manager/vector buffer.
- Call `reset()` first or pass `reset_before_collect=True` to `collect`.
- `collect(n_step=..., n_episode=..., random=False, render=None, reset_before_collect=False, gym_reset_kwargs=None)` requires exactly one positive collection target.
- `n_step` should be a multiple of `env_num`; otherwise extra transitions may be collected.
- `n_episode` smaller than `env_num` can leave some environments idle.
- `random=True` samples from the action space and bypasses policy forward computation.
- `exploration_noise=True` calls the policy's exploration-noise path during collection.
- `on_step_hook(action_batch, rollout_batch)` runs after each environment step and before buffer insertion; mutating `rollout_batch` mutates collected data.
- `on_episode_done_hook(episode_batch)` runs when an episode completes; returned dict fields are written into matching episode transitions and should be arrays with the episode length.
- Episode hooks that return fields are supported for `n_episode` collection; returning fields during `n_step` collection raises an error because episodes can be unfinished.
- `raise_on_nan_in_buffer=True` raises `MalformedBufferError` if `buffer.hasnull()` after collection.

`AsyncCollector` is for asynchronous vector environments. It warns that async collection may collect extra transitions and should not be used with non-async envs.

## Stats Contract

- `CollectStatsBase`: `n_collected_episodes`, `n_collected_steps`.
- `CollectStats`: adds `collect_time`, `collect_speed`, `returns`, `returns_stat`, `lens`, `lens_stat`, `pred_dist_std_array`, and `pred_dist_std_array_stat`.
- `CollectStats.with_autogenerated_stats(...)` builds stats from returns/lens arrays.
- `CollectStats.update_at_step_batch(...)` increments step counts and optional distribution-std stats.
- `CollectStats.update_at_episode_done(...)` records episode length and return.
- `CollectStats.set_collect_time(...)` computes `collect_speed`; zero time logs and sets speed to zero.
- `CollectStats.refresh_all_sequence_stats()` refreshes derived summaries after manual mutation.
- `SequenceSummaryStats.from_sequence(sequence)` returns mean/std/max/min; multi-dimensional inputs are flattened for one summary.
- `compute_dim_to_summary_stats(arr)` returns per-dimension `SequenceSummaryStats` for 2D data.
- `InfoStats` and `TimingStats` are trainer/epoch-level dataclasses that summarize update counts, best rewards, collector counts, and timings.

## Return Computation Touchpoints

Return computation is owned by algorithms, but it depends on buffer chronology and batch fields:

- `Algorithm.compute_nstep_return(batch, buffer, indices, target_q_fn, gamma, n_step)` expects sampled rollout batches and buffer indices that can navigate `next` transitions.
- `Algorithm.compute_episodic_return(...)` and GAE-style preprocessing expect valid `rew`, `terminated`, `truncated`/`done`, and value fields.
- If sampled indices cross malformed episode boundaries, return computation will produce incorrect targets or fail; validate with `buffer.get_buffer_indices`, `prev`, `next`, and known episode starts.
