# Data Collection Workflows

Use these recipes to implement, inspect, and debug Tianshou data flows without relying on the original repository checkout.

## Shape a Batch Safely

```python
from tianshou.data import Batch

batch = Batch(
    obs={"state": [[0.0, 1.0], [2.0, 3.0]], "mask": [1, 0]},
    act=[0, 1],
    rew=[1.0, 0.0],
)
assert len(batch) == 2
first = batch[0]
mini_batches = list(batch.split(size=1, shuffle=False))
torch_batch = batch.to_torch(dtype=None, device="cpu")
np_batch = torch_batch.to_numpy()
```

Rules of thumb:

- Keep the first dimension aligned across fields that should batch together.
- Use nested dictionaries for structured observations; they become nested `Batch` objects.
- Use `Batch.stack([...])` for list-of-transitions to add a new leading dimension.
- Use `Batch.cat([...])` for appending compatible batches along the leading dimension.
- Use `batch.to_dict(recursive=True)` only at boundaries where plain dictionaries are required.
- Use `batch.hasnull()` before learning updates if hooks or partial assignments created new fields.

## Fix Batch Merge/Slice Problems

For a merge or slice error involving nested tensors/object arrays:

1. Print `batch.get_keys()` and nested key sets for every batch before `cat` or `stack`.
2. Confirm every non-empty field has a leading dimension and no scalar-only training field.
3. Convert lists of arrays with equal shapes to `np.asarray`; for ragged arrays, explicitly use `np.array(values, dtype=object)` and avoid tensor conversion.
4. Avoid lists of heterogeneous `torch.Tensor` objects as one field; stack tensors first or keep them under separate keys.
5. Use `axis=0` when stacking batches with partial keys; non-shared keys with `axis != 0` are rejected.
6. After slicing, remember `batch[0]` returns a `Batch` whose leaves can be scalar values; re-batch with `Batch.stack([sample])` if a downstream API needs a leading dimension.

## Add Transitions to ReplayBuffer

```python
import numpy as np
from tianshou.data import Batch, ReplayBuffer

buffer = ReplayBuffer(size=100, random_seed=42)
transition = Batch(
    obs=np.array([0.0, 1.0]),
    act=np.array(1),
    rew=np.array(1.0),
    terminated=np.array(False),
    truncated=np.array(False),
    obs_next=np.array([0.5, 1.5]),
    info={},
)
index, ep_return, ep_len, ep_start = buffer.add(transition)
sampled, sampled_indices = buffer.sample(batch_size=1)
all_data, all_indices = buffer.sample(batch_size=0)
```

Validation steps:

- `len(buffer)` should grow until `buffer.maxsize` and then remain capped.
- `buffer[:]` should contain only available transitions.
- `sampled.get_keys()` should include the rollout keys you expect.
- For vectorized env data, `len(batch)` must equal the number of `buffer_ids` passed to `add`.
- For `ignore_obs_next=True`, ensure downstream code can reconstruct or avoid `obs_next` as needed.

## Choose a Buffer

- Use `ReplayBuffer` for a single environment, unit tests, and local debugging.
- Use `VectorReplayBuffer(total_size, buffer_num)` for `DummyVectorEnv` or `SubprocVectorEnv` with `buffer_num == env_num`.
- Use `PrioritizedReplayBuffer`/`PrioritizedVectorReplayBuffer` when algorithm loss updates priorities through `update_weight(indices, new_weight)`.
- Use `CachedReplayBuffer` when incomplete episodes must live in caches and only complete episodes should move to the main buffer.
- Use `HERReplayBuffer`/`HERVectorReplayBuffer` only for goal-based observations with `observation`, `achieved_goal`, and `desired_goal` keys and a verified reward function.

## Collect with a Policy and Env

```python
from tianshou.data import CollectStats, Collector, VectorReplayBuffer
from tianshou.env import DummyVectorEnv

# env_fns produce Gymnasium envs; policy is a Tianshou Policy or Algorithm.
envs = DummyVectorEnv(env_fns)
buffer = VectorReplayBuffer(total_size=2000, buffer_num=len(envs))
collector = Collector[CollectStats](policy, envs, buffer)
stats = collector.collect(n_step=200, reset_before_collect=True)
```

Use these modes intentionally:

- `collect(n_step=N)`: training-style collection; use when step count matters and no episode-level hook writes whole-episode fields.
- `collect(n_episode=M)`: evaluation or episode-dependent enrichment; use when returns/lens or episode hooks matter.
- `collect(random=True, ...)`: action-space random data smoke or warm-up.
- `reset_before_collect=True`: first call, evaluation collection, or any time collector state may be stale.

Check `stats.n_collected_steps`, `stats.n_collected_episodes`, `stats.returns`, `stats.lens`, `stats.collect_time`, and `stats.collect_speed` after collection.

## Use Hooks Safely

Step hook pattern:

```python
def on_step(action_batch, rollout_batch) -> None:
    rollout_batch.custom_flag = np.ones(len(rollout_batch), dtype=np.float32)
```

Episode hook pattern:

```python
def on_episode_done(episode_batch) -> dict[str, np.ndarray]:
    length = len(episode_batch)
    discounted = np.zeros(length, dtype=np.float32)
    running = 0.0
    for i in range(length - 1, -1, -1):
        running = float(episode_batch.rew[i]) + 0.99 * running
        discounted[i] = running
    return {"mc_return": discounted}
```

Hook guardrails:

- A step hook receives the current ready-env batch and can mutate fields before buffer insertion.
- An episode hook receives one complete episode and must return arrays whose first dimension equals episode length.
- If an episode hook returns fields, collect with `n_episode`, not `n_step`.
- Set `raise_on_nan_in_buffer=True` while developing hooks; call `buffer.isnull().apply_values_transform(np.sum)` to locate bad fields.
- Use `buffer.dropnull()` only after understanding why nulls were introduced.

## Validate Stats

```python
from tianshou.data import SequenceSummaryStats

stats.refresh_all_sequence_stats()
assert stats.n_collected_steps >= len(stats.returns)
if stats.returns.size:
    assert stats.returns_stat is not None
summary = SequenceSummaryStats.from_sequence([1.0, 2.0, 3.0])
```

When stats are manually updated, refresh derived summaries before logging or assertions.

## Debug Return Inputs

For n-step or episodic-return preprocessing failures:

1. Confirm sampled data came from `batch, indices = buffer.sample(...)` and that `indices` are passed along.
2. Confirm `batch.rew`, `batch.terminated`, `batch.truncated`, `batch.obs_next`, and algorithm-required value fields exist.
3. Use `buffer.next(indices)` to inspect bootstrap transitions.
4. Use `buffer.get_buffer_indices(ep_start, ep_stop)` for whole-episode extraction; avoid crossing vector sub-buffer boundaries.
5. For prioritized replay, update priorities only after the learner has used the same sampled `indices`.

## Run the Bundled Smoke

```bash
python skills/tianshou/sub-skills/data-collection/scripts/check_batch_buffer_collector.py
python skills/tianshou/sub-skills/data-collection/scripts/check_batch_buffer_collector.py --skip-collector
python skills/tianshou/sub-skills/data-collection/scripts/check_batch_buffer_collector.py --collector-steps 6 --episodes 2
```

The smoke checks `Batch` slicing/stacking/conversion, `ReplayBuffer.add/sample`, and a minimal `Collector` with NaN validation enabled.
