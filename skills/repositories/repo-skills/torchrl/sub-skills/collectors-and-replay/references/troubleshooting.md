# Collectors and replay troubleshooting

Start with the smallest direct CPU repro. Run [../scripts/smoke_collector.py](../scripts/smoke_collector.py) for collector/device/Evaluator basics and [../scripts/smoke_replay_buffer.py](../scripts/smoke_replay_buffer.py) for storage/sampling/priority basics.

## Collector backend mismatch

Symptoms:

- A task expected direct collection but received a multi-worker or distributed collector.
- `backend_options` values appear ignored or rejected.
- `backend="direct"` fails when `num_collectors > 1`.

Likely causes and fixes:

- Explicit `backend` has priority. Remove it if `num_collectors` should imply process collection.
- `backend_options` must not repeat selector arguments such as `backend` or `num_collectors`; keep backend-specific launcher/resources there.
- A sequence of env factories defines the collector count; any explicit positive `num_collectors` must match the sequence length.
- Use `backend="process"`, `"ray"`, `"rpc"`, `"distributed"`, or `"submitit"` only when the corresponding optional runtime is deliberately available.

## Omitted `sync` in on-policy algorithms

Symptoms:

- PPO/A2C-like training is unstable or uses stale policy data.
- Multi-worker collection seems faster but performance regresses.
- Learner assumes every batch came from the current weights.

Fix:

- For process or distributed collectors in on-policy workflows, pass `sync=True` explicitly.
- For off-policy replay algorithms, `sync=False` can be acceptable, but the learner must tolerate policy lag and should update remote policy weights at a controlled cadence.
- Document the choice next to the collector construction; do not rely on default async behavior.

## Device movement confusion

Symptoms:

- Sampled or collected TensorDict fields are on unexpected devices.
- Policy inputs are copied every step or accelerator memory grows unexpectedly.
- `update_policy_weights_()` appears to be a no-op or copies to the wrong device.

Fix checklist:

1. Identify four roles: `env_device`, `policy_device`, `storing_device`, and fallback `device`.
2. Set all roles to CPU for a minimal repro. Then move only one role at a time.
3. Keep replay storage device aligned with `storing_device` unless the copy is intentional.
4. When training and inference policies live on different devices, call `collector.update_policy_weights_()` after learner updates.
5. Optional CUDA/MPS/ROCm behavior needs backend-specific verification; CPU success only proves the TensorDict/data path.

## Process, fork, and pickling issues

Symptoms:

- Process collectors hang at startup.
- Env or policy factories fail to serialize.
- CUDA contexts or simulator launchers crash in child workers.
- Warnings vanish or become hard to attribute in worker logs.

Fix:

- Use top-level factory functions or picklable callables for env and policy creation.
- Prefer direct collector debugging before process/distributed collectors.
- Avoid constructing fragile simulator or accelerator contexts in the parent before forking; use backend-specific initialization hooks when available.
- For optional Ray/RPC/Submitit setups, add explicit initialization, resource, shutdown, and timeout handling.
- If subprocess warnings are hidden, intentionally change TorchRL warning filtering for the debug run and restore it afterward.

## Collector-to-replay shape problems

Symptoms:

- `extend()` writes fewer/more records than expected.
- `SliceSampler` returns sequences crossing episode or worker boundaries.
- Storage complains about shape or `dim_extend`.
- Variable-length trajectory writes fail with multidimensional storage.

Fix:

- For transition replay, flatten collected batches intentionally before extension unless storage `ndim` preserves fixed leading lanes.
- For `SliceSampler`, keep `track_traj_ids=True` or provide reliable done/end keys.
- Multi-process fixed-frame writes can hide worker boundaries. Use `trajs_per_batch` for clean complete-trajectory writes into replay.
- If `trajs_per_batch` is set, use `LazyTensorStorage(..., ndim=1)` or `LazyMemmapStorage(..., ndim=1)` because trajectories have variable lengths.
- For fixed `[time, env]` or `[time, worker, env]` storage, match `storage.ndim` and `dim_extend` to the written layout.

## Sequence and recurrent sample problems

Symptoms:

- A recurrent loss is applied to burn-in or padding.
- Sequence samples have unexpected flat length.
- Hidden-state refresh writes corrupt stale records.

Fix:

- Remember that `Sequence(length=L, burn_in=B, bootstrap=K)` returns `B + L + K` records per sampled anchor.
- Use `learning_mask & validity_mask` to select loss-bearing real records.
- `dilation` subsamples inside a window; it is not n-step reward aggregation.
- If refreshing stored hidden states asynchronously, use `TensorDictRoundRobinWriter(track_generations=True)` and `update_if_present` with `index_generation`.
- Patch only keys that already exist in storage; conditional updates do not add new fields.

## Prioritized replay update problems

Symptoms:

- Sampling probabilities do not change after loss computation.
- `update_tensordict_priority` silently does nothing.
- Priority tensor shape errors arise with multidimensional or sequence samples.

Fix:

- Use `TensorDictPrioritizedReplayBuffer` or a `PrioritizedSampler` with `TensorDictReplayBuffer`; otherwise `update_tensordict_priority` is not active.
- Ensure `priority_key` matches the sampled/loss TensorDict key, commonly `"td_error"`.
- During extension, include an initial priority key if initial priorities should differ.
- After loss, set the priority key on the sampled TensorDict and call `rb.update_tensordict_priority(sample)`.
- For generic prioritized buffers, call `sample(return_info=True)` and update with `update_priority(info["index"], priority)`.
- Do not drop `index`, `anchor_index`, `validity_mask`, or other metadata before priority writeback in sequence/sample-unit workflows.

## Memmap and checkpoint cleanup

Symptoms:

- `RuntimeError` says a `.memmap` file already exists.
- Checkpoint reload collides with live scratch files.
- Disk fills after repeated smoke or training runs.
- Reloaded buffers have different length or missing storage metadata.

Fix:

- Use a fresh scratch directory for each memmap owner unless `existsok=True` is intentionally safe.
- For checkpoint round trips, restore into a distinct scratch area to avoid colliding with the source buffer's files.
- Keep tiny bounded storage for smoke tests.
- Explicitly remove temporary directories or use a temporary-directory context for tests.
- Decide whether memmaps should survive process exit; set cleanup behavior according to that decision.
- Include writer/sampler state in buffer checkpointing when priority or generation metadata matters.

## HER failures

Symptoms:

- HER relabeling returns unchanged goals or invalid rewards.
- `her_ratio` validation fails.
- Relabeled samples mix goals across episodes.

Fix:

- Confirm the task is goal-conditioned and has achieved-goal, desired-goal, action, and reward keys expected by the HER buffer.
- Keep `her_ratio` in the valid range.
- Ensure episode boundaries are available from done flags or trajectory metadata.
- Provide or verify a reward recomputation function/schema before trusting relabeled rewards.

## Ray optional dependency and service lifecycle

Symptoms:

- `service_backend="ray"` import or initialization fails.
- Ray collector rejects a regular replay buffer.
- Workers appear to write data but the learner buffer stays empty.
- Shutdown leaves Ray actors or ports alive.

Fix:

- Treat Ray as optional. Install and initialize it only for a task that explicitly needs Ray-backed collection or replay.
- A regular in-process replay buffer is serialized to Ray actors and does not become a shared dataset. Use a Ray-owned replay buffer and pass worker clients, or have workers return batches to the driver.
- Choose transport deliberately: Ray object transport for dynamic payloads; distributed Gloo/NCCL transport only for fixed-layout TensorDicts and verified backend availability.
- Only the replay owner should call shutdown on the Ray-backed buffer; worker clients are restricted handles.
- Add timeouts and explicit teardown around Ray collector/evaluator services.
- Do not route generic TorchRL service-registry design questions here; use `llm-vla-and-services` for service internals.

## Evaluator issues

Symptoms:

- Repeated `trigger_eval()` calls are dropped, skipped, or raise while an evaluation is pending.
- Evaluation metrics use stale weights.
- Callback logging races with the training loop.

Fix:

- Understand `busy_policy`: default behavior prevents uncontrolled overlap; use queueing only when stale queued evals are acceptable.
- Pass `weights=current_policy` or a TensorDict weight snapshot to `evaluate()` / `trigger_eval()` when evaluating updated training weights.
- Use `device` to move eval policy weights deliberately.
- Keep `on_result` thread-safe. If it talks to a shared logger or checkpoint writer, add locking or route results through the training loop.
- For process-level simulator initialization, use the optional Ray backend only with its dependency and lifecycle verified.
