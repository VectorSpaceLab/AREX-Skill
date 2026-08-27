# Collaborative Training API Reference

## Purpose

Read this when you need the verified signatures for collaborative averaging, optimizer wrapping, state sharing, or compression strategy selection.

## Core training classes

| Symbol | Verified signature | Notes |
| --- | --- | --- |
| `hivemind.DecentralizedAverager` | `DecentralizedAverager(averaged_tensors, dht, *, start, prefix, target_group_size=None, min_group_size=2, initial_group_bits='', min_matchmaking_time=5.0, request_timeout=3.0, averaging_alpha=1.0, part_size_bytes=524288, allreduce_timeout=None, next_chunk_timeout=None, sender_timeout=None, reducer_timeout=None, compression=NoCompression(), state_compression=NoCompression(), tensor_infos=None, bandwidth=None, min_vector_size=0, auxiliary=False, allow_state_sharing=None, declare_state_period=30, client_mode=None, daemon=True, shutdown_timeout=5)` | Background all-reduce / tensor averaging service. |
| `DecentralizedAverager.step` | `step(self, gather=None, scheduled_time=None, weight=None, timeout=None, allow_retries=True, require_trigger=False, wait=True)` | Returns metadata or a `StepControl`. |
| `DecentralizedAverager.get_tensors` | `get_tensors(self)` | Returns the averaged tensors under a lock. |
| `DecentralizedAverager.load_state_from_peers` | `load_state_from_peers(self, wait=True, timeout=None)` | Pull state from another peer when needed. |
| `hivemind.Optimizer` | `Optimizer(*, dht, run_id, target_batch_size, batch_size_per_step=None, optimizer, params=None, scheduler=None, matchmaking_time=15.0, averaging_timeout=60.0, allreduce_timeout=None, next_chunk_timeout=None, load_state_timeout=600.0, reuse_grad_buffers=False, offload_optimizer=None, delay_optimizer_step=None, delay_grad_averaging=False, delay_state_averaging=True, average_state_every=1, use_local_updates=False, client_mode=None, auxiliary=False, grad_compression=NoCompression(), grad_averager_factory=None, state_averaging_compression=NoCompression(), load_state_compression=NoCompression(), average_opt_statistics=(), extra_tensors=(), averager_opts=None, tracker_opts=None, performance_ema_alpha=0.1, shutdown_timeout=5, verbose=False)` | The main peer-training wrapper around a normal PyTorch optimizer. |
| `hivemind.GradScaler` | `GradScaler(*args, **kwargs)` | Wrapper that cooperates with Hivemind gradient handling. |
| `hivemind.TrainingAverager` | `TrainingAverager(opt, *, average_parameters, average_gradients, average_opt_statistics=(), extra_tensors=(), parameter_names=None, initialize_optimizer=True, **kwargs)` | Lower-level state/gradient averaging wrapper. |
| `hivemind.optim.state_averager.TrainingStateAverager` | `(*, dht, optimizer, params=None, scheduler=None, initialize_optimizer=None, offload_optimizer=False, custom_gradients=False, reuse_tensors=None, delta_rule_averaging=False, performance_ema_alpha=0.1, sync_epoch_when_averaging=False, parameter_names=None, average_opt_statistics=(), extra_tensors=(), status_loglevel=10, **kwargs)` | Manages optimizer state sharing and averaging. |
| `hivemind.optim.grad_averager.GradientAverager` | `GradientAverager(parameters, *, dht, prefix, reuse_grad_buffers=False, accumulate_grads_on=None, client_mode=None, warn=True, averaged_grads=(), **kwargs)` | Gradient-only all-reduce helper. |
| `hivemind.optim.power_sgd_averager.PowerSGDGradientAverager` | `PowerSGDGradientAverager(parameters, averager_rank, *, dht, prefix, reuse_grad_buffers=False, accumulate_grads_on=None, client_mode=None, warn=True, min_compression_ratio=0.5, averaged_grads=None, **kwargs)` | Low-rank gradient compression variant. |
| `hivemind.optim.progress_tracker.ProgressTracker` | `ProgressTracker(dht, prefix, target_batch_size, *, client_mode=None, min_refresh_period=0.5, max_refresh_period=10, default_refresh_period=3, expected_drift_peers=3, expected_drift_rate=0.2, performance_ema_alpha=0.1, metadata_expiration=60.0, status_loglevel=10, private_key=None, daemon=True, start)` | Tracks collaborative training progress in the DHT. |

## All-reduce primitives

| Symbol | Verified signature | Notes |
| --- | --- | --- |
| `AveragingStage` | `IDLE`, `LOOKING_FOR_GROUP`, `AWAITING_TRIGGER`, `RUNNING_ALLREDUCE`, `FINISHED` | Good for reading state-machine transitions. |
| `StepControl` | `StepControl(scheduled_time, deadline, allow_retries, weight, data_for_gather)` | Returned by scheduling APIs. |
| `AllReduceRunner` | `AllReduceRunner(*, p2p, servicer_type, prefix, group_id, tensors, weight=None, ordered_peer_ids, peer_fractions, modes=None, sender_timeout=None, reducer_timeout=None, **kwargs)` | Lower-level all-reduce coordinator. |
| `AveragingMode` | `NODE`, `CLIENT`, `AUX` | Used when reasoning about peer roles. |
| `TensorPartContainer` | `TensorPartContainer(tensors, peer_fractions, compression=NoCompression(), part_size_bytes=524288, tensor_infos=None, return_deltas=True, prefetch=1)` | Tensor partitioning helper used by all-reduce. |
| `TensorPartReducer` | `TensorPartReducer(part_shapes, num_senders)` | Reassembles reduced tensor parts. |

## Compression strategies

| Symbol | Verified signature | Notes |
| --- | --- | --- |
| `NoCompression` | `()` | Default, lossless path. |
| `Float16Compression` | `()` | Common low-cost communication compression. |
| `ScaledFloat16Compression` | `()` | Mean/std-scaled float16 path. |
| `Uniform8BitQuantization` | `()` | Safe 8-bit quantization path. |
| `Quantile8BitQuantization` | `()` | Quantile-based 8-bit quantization. |
| `RoleAdaptiveCompression` | `(*, activation=None, parameter=None, gradient=None, optimizer=None, default=NoCompression())` | Chooses compression based on tensor role. |
| `SizeAdaptiveCompression` | `(threshold, less, greater_equal)` | Chooses compression based on tensor size. |
| `PerTensorCompression` | `(tensor_compressions)` | Chooses compression by tensor key. |
| `BlockwiseQuantization` | `()` | Optional path that depends on `bitsandbytes` at compression time. |

## Behavior notes

- `Optimizer` can perform synchronous or asynchronous collaborative training depending on flags such as `use_local_updates`, `delay_optimizer_step`, and `delay_grad_averaging`.
- `reuse_grad_buffers=True` changes how `zero_grad` should be used; do not call it in the usual way unless the workflow explicitly says so.
- `load_state_from_peers` is how a late-joining peer syncs model or optimizer state before training.
- `ProgressTracker` and `local_epoch` are the right concepts when you need stable global scheduling across uneven peers.
- `BlockwiseQuantization` is public, but the compression path imports `bitsandbytes` lazily and should be treated as optional.

## Validation sources

- Verified against installed signatures from `hivemind` 1.2.0.dev0.
- Cross-checked against `docs/modules/averaging.rst`, `docs/modules/optim.rst`, `docs/user/quickstart.md`, `tests/test_averaging.py`, `tests/test_optimizer.py`, `tests/test_allreduce.py`, and `tests/test_compression.py`.
