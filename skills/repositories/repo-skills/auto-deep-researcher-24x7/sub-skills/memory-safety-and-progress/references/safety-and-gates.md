# Safety signals, stagnation, gates, and truthful failure

These checks are zero-cost, deterministic signals over state and ledger data.
They do not run an experiment, query a model, or prove that a plan is good.
Use them to constrain decisions and explain why a loop is backing off.

## Violation scanner

The exact pure function is:

```python
scan_violations(
    state: dict,
    fail_count: int,
    now: float,
    fail_threshold: int = 3,
    stale_state_hours: int = 6,
) -> list[str]
```

It returns a list of advisory strings:

- If `fail_threshold` is nonzero and `fail_count >= fail_threshold`, emit a
  repeated-no-progress warning. The loop supplies its repeated-plan streak;
  this is not a count of all failed jobs.
- If `state.status == "running"`, `updated_at` is numeric, and
  `(now - updated_at) / 3600 > stale_state_hours`, emit a stale-running warning
  with the measured age. The comparison is strictly greater than the limit.
- A completed, failed, error, idle, or no-PID state is not stale merely because
  its timestamp is old. A non-dict state is treated as `{}`. Invalid timestamp
  text produces no stale warning rather than a fabricated age.

The scanner is advisory. A stale `running` snapshot means “investigate the
backend/process and recover from a crash if confirmed”; it does not mean “mark
completed”. A repeated-plan warning means “change the plan, wait for signal,
or request direction”; it does not mean the latest experiment succeeded.

## Anti-burn rate limiter

The exact helpers are:

```python
seconds_until_allowed(
    timestamps: list[float],
    now: float,
    max_per_hour: int,
    window: int = 3600,
) -> float
prune_timestamps(timestamps: list[float], now: float,
                 window: int = 3600) -> list[float]
```

The limiter is disabled when `max_per_hour <= 0`, returning `0.0` and, in the
loop, writing no cycle-time file. Otherwise, only timestamps with
`now - t < window` count. If the in-window count is below the cap, wait `0.0`.
When the count is at least the cap, sort the recent values and compute:

```text
wait = max(0, window - (now - recent_sorted[len(recent) - max_per_hour]))
```

This waits long enough for the count to become strictly less than the cap,
including when there are excess starts. `prune_timestamps` keeps only the same
strictly in-window values. The loop sleeps in bounded chunks and appends the
new start after pruning. A corrupt `.cycle_times` JSON list is read as empty;
report the corruption rather than treating it as a reliable budget history.

Example: six starts in the last hour with a cap of six and the oldest 3,000
seconds ago require 600 seconds. Eight starts with a cap of six must wait past
enough old starts to leave fewer than six, not merely wait for one timestamp.

## Metric direction and stagnation

Configure `ledger.metric_key`, `ledger.metric_direction`,
`stagnation.threshold_cycles`, and `stagnation.min_delta`. The direction is
`higher_better` for accuracy-like metrics and `lower_better` for loss/error-like
metrics. Metric extraction ignores records whose `metrics` is not a dict,
missing the key, or cannot convert the value to `float`.

`detect_stagnation` returns:

```text
{
  stagnating, metric_key, best, recent_best,
  cycles_since_improvement, n_points, [reason]
}
```

There is no stagnation verdict when `metric_key` is empty (`reason` says no
metric key). With `n_points <= threshold_cycles`, it says there are not enough
metric points yet and is not stagnating. Thereafter, walk metric-bearing
points in order. For higher-is-better, an improvement is
`value > best + min_delta`; for lower-is-better it is
`value < best - min_delta`. Improvement resets `cycles_since_improvement`; a
non-improvement increments it. `stagnating` is true when that count is at
least `threshold_cycles`. `best` is the all-time directional best and
`recent_best` is the directional best in the last threshold-sized points.

Example with `higher_better`, threshold 3, and values
`0.80, 0.81, 0.81, 0.81, 0.81`: the last three non-improvements make the
verdict `stagnating: true`, `best: 0.81`. With `min_delta: 0.01`, tiny changes
such as `0.800, 0.801, 0.802, 0.803, 0.804` do not reset the streak.

A failed entry that contains a real metric remains failed; do not relabel it
as success merely because the metric helper can parse its value. In reports,
show status and metric as separate fields.

## Phase gate math

The exact function is:

```python
check_phase_gate(
    entries: list[dict],
    metric_key: str,
    threshold: float,
    direction: str = "higher_better",
) -> dict
```

No metric yields:

```json
{"gate_met": false, "best_metric": null,
 "blocker_reason": "no metric recorded yet"}
```

Otherwise, calculate the directional best over all numeric metric-bearing
entries. The gate is met when `best >= threshold` for `higher_better`, or
`best <= threshold` for `lower_better`. If not met, preserve the blocker
reason with metric, best value, threshold, and direction. The gate is advisory;
“MET” permits pursuing innovation but does not authorize unsafe execution.

## Failure outcome propagation

A monitor asks the execution backend for final status after liveness ends. If
`success is False`, the result is `status: "failed"` and carries the backend
terminal state. Slurm terminal states such as `TIMEOUT`, `CANCELLED`,
`FAILED`, `NODE_FAIL`, and `OUT_OF_MEMORY` are failure evidence. The loop must
propagate the same outcome as follows:

```text
workspace/state.json:
  {"status": "failed", "terminal_state": "TIMEOUT", ...}

workspace/experiments.jsonl:
  {"status": "failed", "conclusion": "[TIMEOUT] ...", ...}

Dashboard:
  FAILED (TIMEOUT)
```

A terminal `COMPLETED` state is the only Slurm state that yields
`success: true`. If a pid-only backend cannot recover an exit code, its final
status is `unknown`; the existing monitor treats `success is None` as
`completed` for compatibility, but reports the terminal state as `unknown`.
Do not apply that compatibility fallback to a known Slurm failure.

Concrete recovery after a failed Slurm cycle:

1. Preserve `state.status == "failed"` and `terminal_state`.
2. Keep the failed ledger line; append a new hypothesis on retry instead of
   editing the failed line.
3. Read the captured log and scheduler terminal state; classify the cause.
4. Add a concise dead end or insight when it is durable.
5. Only a new cycle with a new observed outcome may change the current status.

## State examples

Healthy completed state:

```json
{
  "cycle": 7,
  "status": "completed",
  "updated_at": 1710000300.0,
  "terminal_state": "COMPLETED",
  "last_metrics": {"acc": 0.82}
}
```

Known failure (must remain failure):

```json
{
  "cycle": 8,
  "status": "failed",
  "updated_at": 1710000400.0,
  "terminal_state": "TIMEOUT",
  "last_metrics": {}
}
```

Stale investigation target (not a result):

```json
{"cycle": 9, "status": "running", "pid": 123, "updated_at": 0.0}
```

For the last example at `now = 7 * 3600` and a six-hour threshold, emit a
stale warning, verify the configured execution backend, and do not write a
success state based on age alone.
