# Monitoring reference

## Zero-LLM lifecycle

`ExperimentMonitor` is constructed as:

```python
ExperimentMonitor(
    poll_interval: int = 900,
    zero_llm: bool = True,
    backend: ExecutionBackend | None = None,
)
```

If no backend is supplied it uses a local backend rooted at the current
workspace. In normal operation the loop passes the configured backend. The
`zero_llm` flag documents the cost contract; monitoring itself does not call a
provider regardless of the flag.

`launch_experiment(command: str, log_file: str, gpu: str | None = None)`
creates `CUDA_VISIBLE_DEVICES` only when `gpu` is provided, parses the command
with shell-like quoting, and calls `backend.launch_command`. It adds
`start_time`, the original command, and `status="running"`, then indexes the
record by returned PID. In Slurm mode the `gpu` argument is not authoritative;
the scheduler's `--gres` allocation wins and the remote submit helper strips
GPU pinning variables.

`wait_for_completion(pid, log_file, notify=True)` follows this contract:

1. Call `backend.is_process_alive(pid)`.
2. While alive, sleep `poll_interval` seconds. After each sleep, safely query
   GPU status and tail five log lines. A failed status/tail query is reduced to
   `{"utilization": "N/A"}` or an empty list, so observability failure does not
   crash the wait loop.
3. When not alive, tail up to 50 lines, compute elapsed time, and call
   `backend.final_status(pid)` through a safe wrapper.
4. Set `status="failed"` only if final `success is False`; set it to
   `"completed"` for true or unknown success. Return PID, status, success,
   terminal state, elapsed hours, joined log tail, and extracted metrics.
5. Update the tracked experiment status and optionally emit a completion log.

The monitor's own result is not a proof that a PID-only process exited with code
zero. For local/SSH, `terminal_state` normally remains `unknown` and
`success` is null. For Slurm, a terminal state observed through `sacct` is
preserved. A backstop-reaped Slurm job also has unknown final state, even though
the wait loop has terminated.

`has_completed_experiments()` checks tracked records without waiting. It marks a
running record completed when the backend reports not alive and returns true for
the first such record. It does not call `final_status`, so use
`wait_for_completion` when truthful terminal-state reporting is required.

## Log and metric behavior

The backend log path is always workspace-relative. During polling, only the
last five lines are read for a compact status message. At termination the last
50 lines are included in the returned `log_tail` (and commonly the state/ledger
handoff). Missing logs are treated as an empty tail; this can mean the job
failed before opening the log, the shared filesystem is stale/unavailable, or
the path is wrong. Distinguish those cases using backend errors and scheduler
state rather than inventing metrics.

Metric extraction scans the final tail from newest line to oldest. For each key,
the first match wins. Recognized patterns are case-insensitive and capture a
numeric-looking token after `loss`, `acc`/`accuracy`, `FGD`, `FID`, `epoch`, or
`step`; values are returned as strings. It is a convenience parser, not a
schema validator. If a metric is absent, leave it absent.

## State handoff

The surrounding controller records `status`, `pid`, `log_file`,
`terminal_state`, `last_training_logs`, `last_metrics`, and elapsed time after
monitoring. A failed Slurm outcome therefore must not be rewritten as
completed by a downstream report. When `success` is null, preserve the
indeterminate state and use the log plus an independent scheduler check before
retrying.

The monitor's completion notification is logging only. It is not an LLM wake-up,
remote daemon, email sender, or scheduler reconciliation mechanism. High-level
THINK/EXECUTE/REFLECT routing belongs to the autonomous-experiments skill.
