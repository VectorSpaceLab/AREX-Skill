# Runner, store, and trainer API reference

## Purpose

Use this for verified signatures of the Agent Lightning control-plane APIs.

## `Trainer`

Verified constructor signature summary:

```python
Trainer(
    *,
    dev=False,
    n_runners=None,
    max_rollouts=None,
    initial_resources=None,
    tracer=None,
    adapter=None,
    store=None,
    runner=None,
    strategy=None,
    port=None,
    algorithm=None,
    llm_proxy=None,
    n_workers=None,
    max_tasks=None,
    daemon=True,
    triplet_exporter=None,
    hooks=None,
)
Trainer.fit(self, agent, train_dataset=None, *, val_dataset=None) -> None
Trainer.dev(self, agent, train_dataset=None, *, val_dataset=None) -> None
```

`n_workers` and `max_tasks` are deprecated compatibility aliases for `n_runners` and `max_rollouts`.

## `Baseline` and algorithm decorators

```python
Baseline(*, n_epochs=1, train_split=0.5, polling_interval=5.0, max_queue_length=4, span_verbosity='keys')
algo(func) -> FunctionalAlgorithm
```

`@algo` functions receive keyword-only `train_dataset` and `val_dataset` in the common pattern. The decorated algorithm can access store, adapter, trainer, LLM proxy, and initial resources through inherited methods.

## Store constructors

```python
InMemoryLightningStore(
    *,
    thread_safe=False,
    eviction_memory_threshold=None,
    safe_memory_threshold=None,
    span_size_estimator=None,
    tracker=None,
    scan_debounce_seconds=10.0,
)
LightningStoreClient(server_address, *, retry_delays=(1.0, 2.0, 5.0), health_retry_delays=(0.1, 0.2, 0.5), request_timeout=30.0, connection_timeout=5.0)
LightningStoreServer(store, host=None, port=None, cors_allow_origins=None, launch_mode='thread', launcher_args=None, n_workers=1, tracker=None)
LightningStoreThreaded(store)
```

## Key store methods

Verified signatures:

```python
enqueue_rollout(input, mode=None, resources_id=None, config=None, metadata=None) -> Rollout
start_rollout(input, mode=None, resources_id=None, config=None, metadata=None, worker_id=None) -> AttemptedRollout
query_rollouts(*, status_in=None, rollout_id_in=None, rollout_id_contains=None, filter_logic='and', sort_by=None, sort_order='asc', limit=-1, offset=0, status=None, rollout_ids=None) -> Sequence[Rollout]
add_resources(resources) -> ResourcesUpdate
update_resources(resources_id, resources) -> ResourcesUpdate
get_next_span_sequence_id(rollout_id, attempt_id) -> int
query_spans(rollout_id, attempt_id=None, *, trace_id=None, trace_id_contains=None, span_id=None, span_id_contains=None, parent_id=None, parent_id_contains=None, name=None, name_contains=None, filter_logic='and', limit=-1, offset=0, sort_by='sequence_id', sort_order='asc') -> Sequence[Span]
```

`status` and `rollout_ids` are legacy aliases; prefer `status_in` and `rollout_id_in` in new code when exact filtering matters.

## `RolloutConfig`

Verified signature:

```python
RolloutConfig(
    *,
    timeout_seconds: float | None = None,
    unresponsive_seconds: float | None = None,
    max_attempts: int = 1,
    retry_condition: list[AttemptStatus] = [],
)
```

- `timeout_seconds` limits total attempt wall-clock time.
- `unresponsive_seconds` limits heartbeat silence.
- `max_attempts` includes the first attempt and must be at least 1.
- `retry_condition` names attempt statuses that should requeue when attempts remain.

## `LitAgentRunner`

```python
LitAgentRunner(
    tracer,
    max_rollouts=None,
    poll_interval=5.0,
    heartbeat_interval=10.0,
    interval_jitter=0.5,
    heartbeat_launch_mode='thread',
    heartbeat_include_gpu=False,
)
LitAgentRunner.step(input, *, resources=None, mode=None, event=None) -> Rollout
LitAgentRunner.run_context(*, agent, store, hooks=None, worker_id=None) -> Iterator[Runner]
```

`heartbeat_include_gpu=False` avoids slow GPU telemetry by default. Enable it only when GPU worker health is part of the task.

## Status type literals

Rollout statuses:

```text
queuing, preparing, running, failed, succeeded, cancelled, requeuing
```

Attempt statuses:

```text
preparing, running, failed, succeeded, unresponsive, timeout
```

See [status-model.md](status-model.md) for transitions.
