# Replay-buffer workflows

Use this reference when the task concerns storage, sampling, prioritization, sequence windows, checkpointing, HER, or collector-to-buffer data flow. For collector topology first, read [collector-workflows.md](collector-workflows.md).

## Compose the buffer explicitly

TorchRL replay buffers are composable. Decide these pieces in order:

1. **Data type**
   - Use `TensorDictReplayBuffer` for TorchRL training data. It accepts only `TensorDictBase` content and injects metadata such as `index` into samples.
   - Use generic `ReplayBuffer` only for non-TensorDict Python data or when you explicitly need `return_info=True` metadata instead of TensorDict metadata keys.
   - Use `TensorDictPrioritizedReplayBuffer` for prioritized TensorDict training data.
2. **Storage**
   - `LazyTensorStorage(max_size, device="cpu", ndim=1)`: in-memory preallocated tensor/TensorDict storage; best default for CPU/GPU smokes and most training loops.
   - `LazyMemmapStorage(max_size, scratch_dir=..., device="cpu", ndim=1, existsok=False, auto_cleanup=None)`: file-backed storage for large datasets or checkpointable buffers. Use a controlled scratch directory and cleanup policy.
   - `ListStorage`: only for irregular Python data; inefficient for tensor-heavy RL.
3. **Sampler**
   - Default random sampler for i.i.d. transitions.
   - `SamplerWithoutReplacement` for epoch-like scans.
   - `PrioritizedSampler` or `TensorDictPrioritizedReplayBuffer` for priority-weighted sampling.
   - `SliceSampler` for contiguous trajectory slices.
4. **Sample unit**
   - Default transition unit samples one record per anchor.
   - `Sequence(length=..., burn_in=..., bootstrap=..., episode_boundary="pad")` expands each anchor into a recurrent training window with masks.
5. **Writer**
   - Default TensorDict round-robin writer is sufficient for most buffers.
   - `TensorDictRoundRobinWriter(track_generations=True)` is required for `update_if_present` generation-safe writeback.
   - Max-value writers are specialized for "keep best record" style datasets, not ordinary online replay.
6. **Transforms, collate, prefetch**
   - `transform` applies on sample; `transform_factory` is used for delayed/pickled initialization.
   - `collate_fn` controls non-TensorDict batching.
   - `prefetch` requires a fixed construction-time `batch_size`; do not use it when callers pass variable sample sizes.

Run [../scripts/smoke_replay_buffer.py](../scripts/smoke_replay_buffer.py) to check the CPU TensorDict, memmap, priority, sequence, and generation paths.

## Storage dimensionality and collector writes

`LazyTensorStorage(..., ndim=1)` treats the first coordinate as storage time and returns flat samples. Increase `ndim` only when the stored TensorDict has fixed extra lanes that must be preserved during sampling, such as `[time, env]` or `[time, worker, env]`.

Rules:

- For a single direct collector writing flat transitions, keep `ndim=1`.
- For a batched environment or synchronized process collector returning fixed-frame `[worker, env, time]` layouts, match `ndim` to the fixed leading storage lanes when using `SliceSampler` over that layout.
- If `trajs_per_batch` is used, trajectories are variable-length flat sequences. Keep storage `ndim=1`; multidimensional storages require fixed lane lengths and are incompatible with variable-length trajectory writes.
- `dim_extend` controls which dimension an `extend()` call consumes. When using multidimensional storage, set it intentionally and keep it consistent with storage `ndim`.

## Transition replay pattern

```python
from torchrl.data import LazyTensorStorage, TensorDictReplayBuffer

rb = TensorDictReplayBuffer(
    storage=LazyTensorStorage(100_000),
    batch_size=256,
)
rb.extend(collected_td.reshape(-1))
sample = rb.sample()
assert "index" in sample.keys()
```

For replay buffers used as iterables, construction-time `batch_size` controls each yielded batch. Prefer construction-time `batch_size` if the size is stable across the experiment.

## Sequence sample units for recurrent learners

`Sequence(length, episode_boundary="pad", burn_in=0, bootstrap=0, dilation=1)` expands each sampled anchor into a window. With `B` anchors, the flat output has `B * (burn_in + length + bootstrap)` records.

Use it when a recurrent or sequence learner needs:

- **burn-in** records to reconstruct hidden state before loss-bearing steps;
- **learning** records of length `length`;
- **bootstrap** records after the learning region for target estimators;
- **masks** to avoid applying loss to padding, burn-in, or invalid records.

Expected metadata:

- `learning_mask`: true on records where the loss can be applied.
- `validity_mask`: true on real records; false on padding introduced by boundary handling.
- `anchor_index`, `sequence_id`, `step_in_sequence`, and `index` for tracing sampled windows.

Practical recurrent recipe:

```python
from torchrl.data import LazyTensorStorage, TensorDictReplayBuffer
from torchrl.data.replay_buffers import Sequence

rb = TensorDictReplayBuffer(
    storage=LazyTensorStorage(20_000),
    batch_size=32,
    sample_unit=Sequence(length=16, burn_in=8, bootstrap=4, episode_boundary="pad"),
)
# after filling rb
sample = rb.sample()
loss_mask = sample["learning_mask"] & sample["validity_mask"]
```

The sample unit selects records and produces masks; it does not run the recurrent module and does not compute target values. Route recurrent policy details to `modules-and-policies` and value-estimator details to `objectives-and-training`.

## Slice sampling for trajectories

Use `SliceSampler` when the learner needs contiguous sub-trajectories from storage rather than independent transitions.

Boundary sources:

- `("collector", "traj_ids")` when data came from a TorchRL collector with `track_traj_ids=True`.
- `("next", "done")`, `("next", "terminated")`, or `("next", "truncated")` when only done flags exist.
- Explicit episode or trajectory keys in offline datasets.

Pitfalls:

- If fixed-frame multi-process batches are written without complete-trajectory assembly, adjacent storage records can belong to unrelated workers and episodes. `SliceSampler` cannot see invisible worker batch boundaries.
- For clean slices from process collectors, prefer `trajs_per_batch` so workers write complete flat trajectories to the buffer.
- `strict_length=False` keeps short trajectories or slices; otherwise short segments may be dropped.

## Prioritized replay

Prefer TensorDict-specific prioritized replay for RL losses:

```python
from torchrl.data import LazyTensorStorage, TensorDictPrioritizedReplayBuffer

rb = TensorDictPrioritizedReplayBuffer(
    alpha=0.7,
    beta=0.5,
    storage=LazyTensorStorage(100_000),
    batch_size=256,
    priority_key="td_error",
)
rb.extend(data_with_td_error)
sample = rb.sample()
loss_td = loss_module(sample)
sample["td_error"] = loss_td["td_error"].detach()
rb.update_tensordict_priority(sample)
```

Notes:

- TensorDict buffers add `index` to samples; prioritized TensorDict samples also carry importance weights such as `priority_weight`.
- `priority_key` must be present during extension if you want initial priorities to reflect the data.
- After loss computation, update the priority key in the sampled TensorDict and call `update_tensordict_priority(sample)`.
- Generic `PrioritizedReplayBuffer` requires `sample(..., return_info=True)` to retrieve indices, then `update_priority(info["index"], new_priority)`.
- If `Sequence` expands anchors into windows, TorchRL reduces per-record priorities back to anchors where possible. Ensure the sampled TensorDict still has the metadata keys needed for priority writeback.

## Generation-safe conditional updates

Use generation tracking when a sampled index may be overwritten before a delayed writeback arrives.

```python
from torchrl.data import LazyTensorStorage, TensorDictReplayBuffer, TensorDictRoundRobinWriter

rb = TensorDictReplayBuffer(
    storage=LazyTensorStorage(1000),
    writer=TensorDictRoundRobinWriter(track_generations=True),
    batch_size=32,
)
sample = rb.sample()
result = rb.update_if_present(
    index=sample["index"],
    generation=sample["index_generation"],
    patch={"hidden_state": refreshed_hidden_state},
)
```

Constraints:

- `update_if_present` requires a writer that tracks generations.
- The patch can only target existing tensor fields in storage; it does not add new TensorDict keys.
- `index_generation` is a staleness guard, not a global timestamp ordering all slots.
- Versioned conditional updates add `version_key`, `version`, and `require_newer` when several workers race to write refreshed fields. The version key must name an existing per-record scalar field and must not also appear in the patch.

## LazyMemmapStorage and checkpoints

Use `LazyMemmapStorage` when in-memory storage is too large or when checkpointing large tensor data is important.

Checklist:

- Use a caller-controlled scratch directory or a temporary directory for tests.
- Decide cleanup explicitly. Temporary smoke scripts can rely on `TemporaryDirectory`; long jobs should document whether memmaps must survive process exit.
- Avoid reusing a scratch directory with existing memmap files unless `existsok=True` is intended.
- For checkpoint round trips, create a distinct storage scratch area for the restored buffer to avoid filename collisions with the source memmaps.
- If storage content is large, checkpointing can be asynchronous or slow; keep smoke tests tiny.

## HER notes

`HERReplayBuffer` and `HindsightStrategy` support hindsight relabeling for goal-conditioned data. Use this route when the data has achieved-goal / desired-goal fields and a reward function suitable for recomputation.

Key checks before using HER:

- Validate `her_ratio` is in range.
- Confirm the buffer can detect episode ends; HER relabeling depends on future achieved goals in the same trajectory.
- Confirm goal and reward keys match the task's TensorDict schema.
- Do not silently reuse HER recipes for ordinary transition replay without goal-conditioned data.

## Ray and service-backed replay

Replay buffers default to direct service behavior where `buffer.client() is buffer`. `service_backend="ray"` creates a Ray-owned replay buffer and `client()` returns a restricted, picklable handle for workers.

Use Ray-backed replay only when all of these are true:

- Ray is installed and intentionally initialized for the job.
- The worker topology needs a shared owner, not serialized independent copies.
- Payload transport is selected deliberately: flexible Ray object transport for dynamic Python-ish payloads, or distributed Gloo/NCCL transport for fixed-layout TensorDicts.
- The owner lifecycle is clear: only the owner shuts down the actor.

For Ray collectors, a regular in-process replay buffer is not a valid shared dataset; each actor would receive a serialized copy. Use a Ray-owned buffer or have workers return batches to the driver.

## Source-script decisions

- Adapted safe replay patterns into [../scripts/smoke_replay_buffer.py](../scripts/smoke_replay_buffer.py): TensorDict storage, memmap checkpoint round trip, priority update, `Sequence` masks, and generation-safe update.
- Long recurrent `SliceSampler` pipelines are reference-only here because they require actor/RNN construction and a training loop owned by other sub-skills.
- Ray/distributed replay examples are reference-only because they require optional Ray/process services and lifecycle management beyond a safe generic helper.
