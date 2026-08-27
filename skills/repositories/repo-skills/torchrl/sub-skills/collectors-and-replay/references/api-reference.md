# Collectors and replay API reference

This file records installed API facts and public import paths used by the workflow references. Treat optional distributed and service-backed entries as capability routes, not verified local backend availability.

## Collector imports

```python
from torchrl.collectors import Collector, Evaluator
# Concrete collector classes and distributed implementations are available for
# implementation-specific code, but new construction should prefer Collector.
```

### `Collector`

Verified construction signature excerpt:

```python
Collector(
    create_env_fn,
    policy=None,
    *,
    policy_factory=None,
    backend=None,                      # "direct", "process", "ray", "rpc", "distributed", "submitit"
    backend_options=None,
    num_collectors=None,
    sync=None,
    frames_per_batch,
    total_frames=-1,
    device=None,
    storing_device=None,
    policy_device=None,
    env_device=None,
    create_env_kwargs=None,
    max_frames_per_traj=None,
    init_random_frames=None,
    reset_at_each_iter=False,
    postproc=None,
    split_trajs=None,
    track_traj_ids=True,
    exploration_type="random",
    return_same_td=False,
    reset_when_done=True,
    replay_buffer=None,
    extend_buffer=True,
    compile_policy=None,
    cudagraph_policy=None,
    weight_updater=None,
    weight_sync_schemes=None,
    weight_recv_schemes=None,
    track_policy_version=False,
    trajs_per_batch=None,
    trajs_per_write=None,
    traj_format=None,                  # "padded" or "cat" when trajs_per_batch is set
    auto_register_policy_transforms=None,
    pre_collect_hook=None,
    post_collect_hook=None,
    compact_obs=False,
    **kwargs,
)
```

Common methods and fields to look for in code:

- Iterate over the collector for yielded batches.
- `start()` for background/asynchronous collection.
- `shutdown()` for ordinary cleanup.
- `async_shutdown()` after `start()`.
- `update_policy_weights_(...)` after learner parameter updates when workers or copied inference policies are used.
- Worker/broadcast helpers such as `map_fn` and `get_distant_attr` on multi-worker collectors.

### Backend selector values

| `backend` | Intended placement | Notes |
| --- | --- | --- |
| `None` / `"direct"` | Current process | Best smoke/debug default; no optional service dependency |
| `"process"` or `num_collectors=N` | Local worker processes | `sync` should be explicit; workers need picklable env/policy factories |
| `"ray"` | Ray actors | Optional Ray dependency; use Ray-owned replay buffer for direct actor writes |
| `"rpc"` | PyTorch RPC workers | Optional distributed setup; configure launcher/options |
| `"distributed"` | Process-group distributed collector | Requires launcher and backend options such as Gloo/NCCL |
| `"submitit"` | Submitit launcher shortcut | Scheduler/launcher workflow; optional dependency and cluster assumptions |

### `Evaluator`

Verified construction signature excerpt:

```python
Evaluator(
    env,
    policy=None,
    *,
    policy_factory=None,
    num_trajectories=10,
    max_steps=None,
    frames_per_batch=None,
    collector_cls=None,
    collector_kwargs=None,
    weight_sync_schemes=None,
    log_prefix="eval",
    reward_keys=("next", "reward"),
    done_keys=("next", "done"),
    device=None,
    exploration_type="deterministic",
    metrics_fn=None,
    dump_video=True,
    on_result=None,
    busy_policy="skip",
    backend="thread",
    init_fn=None,
    num_gpus=1,
    ray_kwargs=None,
)
```

Useful methods:

- `evaluate(weights=None, step=None)`: blocking evaluation.
- `trigger_eval(weights=None, step=None)`: non-blocking start.
- `poll(timeout=None)` and `wait(timeout=None)`: retrieve async result.
- `shutdown()`: stop background resources.

## Replay-buffer imports

```python
from torchrl.data import (
    HERReplayBuffer,
    HindsightStrategy,
    LazyMemmapStorage,
    LazyTensorStorage,
    OfflineToOnlineReplayBuffer,
    PrioritizedReplayBuffer,
    PrioritizedSampler,
    RayReplayBuffer,
    ReplayBuffer,
    RoundRobinWriter,
    SamplerWithoutReplacement,
    Sequence,
    SliceSampler,
    SliceSamplerWithoutReplacement,
    TensorDictPrioritizedReplayBuffer,
    TensorDictReplayBuffer,
    TensorDictRoundRobinWriter,
)
```

The same objects are also exposed under `torchrl.data.replay_buffers` for more specific imports.

## Core replay buffer classes

### `ReplayBuffer`

Verified signature shape:

```python
ReplayBuffer(*args, use_ray_service=False, service_backend=None, service_backend_options=None, **kwargs)
```

Important keyword arguments include `storage`, `sampler`, `writer`, `collate_fn`, `pin_memory`, `prefetch`, `transform`, `transform_factory`, `batch_size`, `dim_extend`, `consume_after_n_samples`, `delayed_init`, `transport`, and `transport_options`.

Use generic `ReplayBuffer` for non-TensorDict payloads or when you want `(sample, info)` metadata via `return_info=True`.

### `TensorDictReplayBuffer`

TensorDict-specific wrapper around `ReplayBuffer`.

Important behavior:

- Accepts only `TensorDictBase` content.
- Default writer is TensorDict round-robin.
- Samples include metadata keys such as `index`; with generation tracking they also include `index_generation`.
- `priority_key` defaults to `"td_error"` and is used when the sampler is prioritized.

### `TensorDictPrioritizedReplayBuffer`

TensorDict wrapper for prioritized replay. Requires:

```python
TensorDictPrioritizedReplayBuffer(
    alpha: float,
    beta: float,
    eps: float = 1e-8,
    storage=None,
    batch_size=None,
    priority_key="td_error",
    sampler_device=None,
    sync=True,
    ...,
)
```

Use `update_tensordict_priority(sample)` after updating the sample's priority key.

### `PrioritizedReplayBuffer`

Generic prioritized replay buffer. Use `sample(..., return_info=True)` to retrieve `info["index"]`, then call `update_priority(index, priority)`.

## Storage classes

### `LazyTensorStorage`

Verified signature:

```python
LazyTensorStorage(
    max_size,
    *,
    device="cpu",
    ndim=1,
    compilable=False,
    consolidated=False,
    shared_init=False,
    cleanup_memmap=True,
)
```

Use as the default storage for tensor and TensorDict replay. `ndim` defines how many storage coordinates are consumed by writes and samples.

### `LazyMemmapStorage`

Verified signature:

```python
LazyMemmapStorage(
    max_size,
    *,
    scratch_dir=None,
    device="cpu",
    ndim=1,
    existsok=False,
    compilable=False,
    shared_init=False,
    auto_cleanup=None,
)
```

Use for large file-backed buffers or checkpoint workflows. Pass a dedicated scratch directory for reproducible cleanup. Avoid collisions unless `existsok=True` is intended.

## Samplers and sample units

### `Sequence`

Verified signature:

```python
Sequence(
    length: int,
    episode_boundary="pad",    # "pad", "stop", or "include_reset"
    done_key=("next", "done"),
    burn_in=0,
    bootstrap=0,
    dilation=1,
)
```

Returns windows of `burn_in + length + bootstrap` records per anchor and produces masks/metadata for recurrent learners.

### `SliceSampler`

Used for contiguous slices from trajectories. Key configuration concepts:

- choose a trajectory key such as `("collector", "traj_ids")` or done/end keys;
- set a slice length or number of slices according to the learner;
- decide whether short slices should be kept with `strict_length=False`;
- ensure storage layout matches fixed lanes or flat complete trajectories.

### `PrioritizedSampler`

Used directly with generic or TensorDict replay buffers when not using `TensorDictPrioritizedReplayBuffer`. Requires max capacity plus prioritization hyperparameters such as `alpha` and `beta`.

## Writers and conditional updates

- `RoundRobinWriter` and `TensorDictRoundRobinWriter`: default online replay writers.
- `TensorDictRoundRobinWriter(track_generations=True)`: emits `index_generation` and enables `ReplayBuffer.update_if_present(...)`.
- `TensorDictMaxValueWriter`: specialized for keeping values by score/key; do not use as the ordinary online replay default.

Generation update signature pattern:

```python
result = rb.update_if_present(
    index=sample["index"],
    generation=sample["index_generation"],
    patch={"existing_key": new_value},
    # optional version_key=..., version=..., require_newer=True,
)
```

The patch must target keys already present in storage.

## Optional replay families

- `OfflineToOnlineReplayBuffer` and `prefill_replay_buffer`: use when mixing offline and online data. Check offline dataset ownership and transform compatibility before wiring into a learner.
- `HERReplayBuffer` and `HindsightStrategy`: use for goal-conditioned hindsight replay when achieved/desired goal and reward recomputation keys are known.
- `RayReplayBuffer` and `service_backend="ray"`: use only when Ray is installed and a shared replay owner is needed by collectors or workers.

## API evidence status

CPU import, signature inspection, direct collector smoke, replay smoke, and Evaluator smoke were verified. Optional CUDA kernels, Ray services, RPC, distributed process groups, Submitit, NCCL, simulator-specific workers, and accelerator-backed transports are routes with documented constraints, not verified by the CPU smokes.
