# Rollout and attempt status model

## Purpose

Use this when debugging stuck work, retries, timeouts, or worker liveness.

## Entities

- A **rollout** is the user-level task execution request.
- An **attempt** is one actual execution of a rollout.
- A rollout may have multiple attempts when retries are enabled.
- Spans act as execution records and heartbeats.

## Rollout statuses

| Status | Meaning |
| --- | --- |
| `queuing` | Work was enqueued and has not been claimed. |
| `preparing` | A runner claimed or started an attempt but has not emitted its first span. |
| `running` | At least one span was recorded for the active attempt. |
| `succeeded` | The latest attempt completed successfully. |
| `failed` | Work reached a terminal failure with no retry remaining. |
| `cancelled` | Work was explicitly cancelled. |
| `requeuing` | The latest attempt failed/timed out/became unresponsive and retry policy allows another attempt. |

## Attempt statuses

| Status | Meaning |
| --- | --- |
| `preparing` | Attempt was created and is waiting for first progress. |
| `running` | Attempt has emitted at least one span/heartbeat. |
| `succeeded` | Runner completed successfully. |
| `failed` | Runner raised or marked failure. |
| `unresponsive` | Heartbeat silence exceeded `unresponsive_seconds`. |
| `timeout` | Total attempt wall time exceeded `timeout_seconds`. |

## Lifecycle overview

Typical queue path:

```text
enqueue_rollout -> rollout=queuing
runner dequeue_rollout -> rollout=preparing, attempt=preparing
first add_span/add_otel_span -> rollout=running, attempt=running
runner update_attempt(succeeded) -> rollout=succeeded, attempt=succeeded
```

Retry path:

```text
attempt failed/timeout/unresponsive
if status in retry_condition and attempt sequence < max_attempts:
    rollout=requeuing
    next dequeue_rollout creates a new attempt
else:
    rollout=failed
```

## RolloutConfig examples

Retry explicit failures and timeouts up to three total attempts:

```python
cfg = agl.RolloutConfig(
    timeout_seconds=600,
    unresponsive_seconds=120,
    max_attempts=3,
    retry_condition=["failed", "timeout"],
)
rollout = await store.enqueue_rollout(input=task, config=cfg)
```

No retries:

```python
cfg = agl.RolloutConfig(max_attempts=1, retry_condition=[])
```

## Query recipes

Find unfinished rollouts:

```python
pending = await store.query_rollouts(status_in=["queuing", "requeuing", "preparing", "running"])
```

Find latest spans for a rollout:

```python
spans = await store.query_spans(rollout_id, attempt_id="latest")
```

Check attempts:

```python
attempts = await store.query_attempts(rollout_id)
```

## Debug checklist

1. If status is `queuing`, check that a runner is running and polling the same store.
2. If status is `preparing`, check runner startup, first trace emission, and agent initialization.
3. If status is `running`, inspect recent spans and heartbeat settings.
4. If status is `unresponsive`, check whether the runner is alive and whether a later span revived it.
5. If status is `timeout`, compare the task duration with `timeout_seconds`.
6. If status is `requeuing`, inspect `max_attempts`, `retry_condition`, and previous attempt errors.
7. If status is terminal but no reward exists, inspect the spans before changing the algorithm.
