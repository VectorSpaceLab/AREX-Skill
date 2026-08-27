# Collector workflows

Use this reference after an environment and a policy already exist. If the user still needs to build either one, route to `envs-and-transforms` or `modules-and-policies` first.

## Unified collector selector

Prefer `torchrl.collectors.Collector` as the construction front door. It returns the concrete direct, multi-process, or distributed implementation implied by the selector but keeps the training loop code stable.

Decision sequence:

1. **Direct CPU or single-device rollout**: `Collector(env_or_factory, policy, backend="direct", frames_per_batch=..., total_frames=...)`. Use this first for smoke tests, small environments, and debugging TensorDict shapes.
2. **Local multi-process rollout**: pass `num_collectors=N` or `backend="process"`. Use `sync=True` for on-policy algorithms where the learner must train on current-policy data; use `sync=False` only when policy lag is acceptable.
3. **Ray / RPC / distributed / Submitit**: pass `backend="ray"`, `"rpc"`, `"distributed"`, or `"submitit"` plus `backend_options`. Treat these as optional-service workflows: they require the backend dependency and a lifecycle plan for worker startup, teardown, resources, and data transport.
4. **Scoped service backend**: if a surrounding TorchRL service context is in use, make selector precedence explicit in code comments. Explicit `backend=` wins over service context; `num_collectors` implies process only when no explicit backend is passed.

Important selection rules:

- Omitted `sync` on non-direct backends defaults to asynchronous behavior. Do not leave it implicit for PPO, A2C, GRPO-style on-policy batches, or any workflow that assumes data came from the latest policy.
- Explicit `backend="direct"` accepts at most one collector.
- If `create_env_fn` is a sequence of factories, its length determines the number of collectors; a positive explicit `num_collectors` must match it.
- For broad `isinstance` checks, target the common collector base type rather than the direct `Collector` concrete class, because process and distributed selectors return different concrete classes.

## Sync and async choices

Use this table when a task says only "make collection faster" or "use async collection":

| Need | Collector choice | Why |
| --- | --- | --- |
| Debug one environment/policy, reproduce shapes, run CPU smoke | Direct collector | No worker serialization, easiest errors, no optional services |
| On-policy algorithm batch | `num_collectors=N, sync=True` | All workers contribute to each synchronized batch before training |
| Off-policy replay training | `num_collectors=N, sync=False` or direct `start()` with replay | Learner can tolerate stale collection policy and train while collection proceeds |
| High-throughput Ray actors | `backend="ray"` plus a Ray-owned replay buffer | Avoids each actor owning an independent serialized in-process buffer |
| Multi-node launcher or scheduler | `backend="distributed"` / `"submitit"` | Requires launcher/process-group options under `backend_options` |

If a training loop updates parameters while workers are collecting, call `collector.update_policy_weights_()` at the right cadence or configure a weight-updater/sync scheme. For local worker collectors, remote policies otherwise keep stale weights.

## Core rollout knobs

- `frames_per_batch`: number of frames yielded, or internal polling granularity when complete trajectories are requested.
- `total_frames`: total collection budget; `-1` means keep collecting until the caller shuts down.
- `init_random_frames`: use environment random actions before policy rollout for off-policy warmup.
- `max_frames_per_traj`: force environment reset after a fixed number of frames.
- `reset_at_each_iter`: reset environments between yielded batches.
- `track_traj_ids=True`: default; writes `("collector", "traj_ids")`, needed by `SliceSampler` and trajectory splitting.
- `split_trajs=True`: yields padded trajectory batches with a mask; only use when the learner consumes padded whole trajectories.
- `postproc`: transform yielded batches. Use this for data transformation, not collector hooks.
- `pre_collect_hook` / `post_collect_hook`: instrumentation or worker-local side effects. Hook exceptions stop collection.

## Device and data movement decisions

Collector device terms are easy to confuse:

- `env_device`: where environment tensors live and stepping occurs when the env supports device placement.
- `policy_device`: where the inference policy runs.
- `storing_device`: where collected TensorDict batches are materialized before return or buffer write.
- `device`: default for unspecified device slots.

Practical rules:

1. For a first repro, set all four to CPU or leave them consistently unset.
2. When training on one accelerator and collecting on another, make `policy_device` explicit and call `update_policy_weights_()` after learner updates.
3. Keep `storing_device` aligned with the replay storage device when possible; otherwise inspect whether copies occur before sampling.
4. Do not claim CUDA, MPS, ROCm, NCCL, or Ray distributed transport correctness from a CPU smoke. Those are optional backend checks.

Run [../scripts/smoke_collector.py](../scripts/smoke_collector.py) for a safe direct CPU check that exercises explicit device arguments.

## Collector plus replay buffer

For off-policy training, a collector can either yield data for the loop to extend into a buffer, or write directly into `replay_buffer=`.

Manual extension pattern:

```python
from torchrl.collectors import Collector
from torchrl.data import LazyTensorStorage, TensorDictReplayBuffer

rb = TensorDictReplayBuffer(storage=LazyTensorStorage(100_000), batch_size=256)
collector = Collector(make_env, policy, frames_per_batch=512, total_frames=50_000)
for batch in collector:
    rb.extend(batch.reshape(-1))
    sample = rb.sample()
```

Direct write pattern:

```python
collector = Collector(
    make_env,
    policy,
    replay_buffer=rb,
    frames_per_batch=512,
    total_frames=-1,
    sync=False,        # off-policy only unless explicitly justified
)
collector.start()
try:
    while training:
        sample = rb.sample()
        # update model, then refresh remote policy when needed
        collector.update_policy_weights_()
finally:
    collector.async_shutdown()
```

Trajectory-safe replay rules:

- For ordinary i.i.d. transition sampling, flatten or reshape collected batches before extending storage if the collector returned extra worker or environment lanes.
- For `SliceSampler`, preserve real trajectory boundaries. `track_traj_ids=True` gives the sampler `("collector", "traj_ids")`.
- Multi-process fixed-frame writes can put unrelated worker/episode segments next to each other. Prefer `trajs_per_batch` when sampling contiguous trajectory slices from a buffer.
- If `trajs_per_batch` is set, each worker writes complete trajectories as flat 1-D variable-length sequences. Keep replay storage `ndim=1`; do not use multidimensional storage for variable-length trajectory writes.
- `set_truncated=True` can mark fixed-frame batch boundaries, but it introduces artificial truncations that value estimators must handle. Prefer complete trajectories when the learner needs trajectory integrity.

## Complete trajectory collection

Use `trajs_per_batch` when the training unit is a whole episode or a clean episode slice:

```python
collector = Collector(
    make_env,
    policy,
    frames_per_batch=200,
    total_frames=-1,
    trajs_per_batch=16,
    traj_format="cat",  # flat, unpadded, contiguous completed episodes
)
for batch in collector:
    done = batch["next", "done"]
```

`traj_format="padded"` gives `[num_trajs, max_len]` batches plus a collector mask; it is convenient for per-episode reductions but may waste memory when lengths vary. `traj_format="cat"` is usually better for replay and large frames because it avoids padding.

## Evaluator workflow

`torchrl.collectors.Evaluator` decouples evaluation rollouts from training. Use it when a task asks for periodic evaluation, async eval, callback metrics, or moving evaluation to a separate device/process.

Minimal synchronous use:

```python
from torchrl.collectors import Evaluator

evaluator = Evaluator(make_eval_env, eval_policy, num_trajectories=4, max_steps=1000)
metrics = evaluator.evaluate(weights=current_policy)
evaluator.shutdown()
```

Async use:

```python
evaluator.trigger_eval(weights=current_policy, step=frames_seen)
result = evaluator.poll()
# or evaluator.wait(timeout=60)
```

Evaluator notes:

- Default backend is a thread. `backend="ray"` is optional and needs Ray plus a Ray lifecycle plan.
- `busy_policy="error"` prevents silently queueing stale evaluations. Use `"queue"` only when desired.
- `metrics_fn` extracts custom metrics from rollout TensorDicts; `on_result` can log or checkpoint after completion.
- `device` controls where evaluation policy weights move before rollout.

## Source-script decisions

- Adapted safe direct collector, explicit-device, replay integration, and Evaluator behavior into [../scripts/smoke_collector.py](../scripts/smoke_collector.py).
- Distributed, Ray, RPC, Submitit, and multi-weight-update examples are reference-only for this runtime sub-skill because they require optional packages, process/service lifecycle management, or hardware/resource assumptions that are not safe generic smokes.
- Device-combination training examples are reference-only because they run optimization and often require accelerator availability; this sub-skill keeps the deterministic helper to collection and buffer integration only.
