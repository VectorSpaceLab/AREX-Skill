# Troubleshooting memory, safety, and progress state

Use these runbooks for predictable failures. They are read-first and
append-first: preserve evidence before attempting recovery.

| Symptom | Likely cause | Recovery |
|---|---|---|
| Ledger has fewer entries than physical lines | Blank or malformed JSONL lines | Count valid/malformed lines with the inspector; preserve the original file and append a new valid record. Do not rewrite away the malformed line. |
| `summary()` says `no metrics` | Missing/non-dict/non-numeric metric field | Report the status separately, verify the configured metric key, and wait for a real numeric result. |
| Stagnation says “not enough metric points” | `n_points <= threshold_cycles` | Treat it as insufficient evidence, not improvement or failure; keep collecting metric-bearing cycles. |
| Stagnation is surprising | Wrong direction or `min_delta` | Confirm `higher_better` vs `lower_better`, threshold, and numeric units. Recompute; do not edit historical entries. |
| Gate is not met | No metric or directional best misses threshold | Show `best_metric`, threshold, and direction. Change the experiment plan or request a gate decision; never claim promotion. |
| `DEAD_ENDS.md` / `INSIGHTS.md` is large | Rotation threshold exceeded | List `.bak` archives and read the live tail. The archive is the full history; retain it. |
| Journal rotation did not create a backup | Permission, disk, or path error | Preserve the live file, check access/space using safe read-only diagnostics, and retry only after the filesystem issue is resolved. Never truncate manually. |
| Journal tail is empty but file exists | File unreadable, directory in place of file, or no content | Report unreadable/type error; inspect permissions and archive list. Do not infer “no insight”. |
| State says `running` for too long | Process died, backend is unreachable, or state update was missed | Run the inspector with a known `--now`; verify the configured backend/process. Keep status unresolved until an outcome is observed. |
| Dashboard shows `IDLE` for a known failure | Export read an old/malformed snapshot or failure was overwritten | Restore/report the latest valid failed state and terminal state. A known Slurm failure must render `FAILED (<state>)`. |
| Slurm job is `TIMEOUT`, `CANCELLED`, or `OUT_OF_MEMORY` | Scheduler terminal failure | Keep state/ledger/dashboard failed, prefix the ledger conclusion with terminal state, capture logs, and create a new hypothesis for any retry. |
| `.cycle_counter` is missing or non-integer | New project or interrupted/manual edit | Report counter invalid; recover from an external trusted record or start at an explicitly approved count. Do not silently invent a completed-cycle count. |
| Rate limiter refuses to start | Enough valid timestamps are inside the rolling window | Show computed wait and cap. Wait or ask for a policy change; do not delete timestamps to bypass budget. |
| `.cycle_times` is malformed | Partial/manual edit | Report that historical rate evidence is incomplete; preserve the file and use a conservative operator decision. A runtime loader may use an empty list, but the report must disclose that fallback. |
| Export is disabled | `obsidian.enabled: false` | Report disabled. Do not claim vault/local notes were refreshed. Enable only with an explicit configuration decision. |
| Vault path is unavailable | Missing, unwritable, or misconfigured vault | Prefer the configured local fallback only if the exporter is intentionally configured to do so; otherwise report export failure and provide state directly. Do not create a replacement vault. |
| Daily note duplicates an event | Manual refresh or repeated invocation | Label events by `event_type` and timestamp; treat the append-only note as an event log, not a deduplicated database. |

## Malformed ledger procedure

1. Copy or snapshot the project outside the live runtime area if an operator
   needs a repair copy.
2. Run the read-only inspector and record valid count, malformed count, and
   the last valid entries.
3. Leave malformed lines in place so line order and forensic evidence survive.
4. Append a new record through the normal ledger interface; do not parse and
   rewrite the entire file.
5. In reports, say “N valid records, M malformed lines skipped”.

A malformed line cannot erase earlier valid lines because the reader processes
independent lines. A truncated final line is handled the same way.

## Journal rotation procedure

1. Check the live header, rotation marker, and newest entries.
2. Enumerate all matching `.bak` files and sort by name/time; duplicate
   timestamps are expected to gain `.1`, `.2`, and so on.
3. Verify that the newest archive contains the pre-rotation content before
   treating the rotation as complete.
4. If the archive is present, use it as durable history and the live file as a
   context tail.
5. If no archive is present after an oversized write, preserve the live file,
   report the OS error if available, and fix permissions/space before retrying.

Never “recover” by deleting the live journal or archives. Rotation is designed
to avoid losing history, even though the live file only keeps a bounded tail.

## Failure/status reconciliation

If state, ledger, and dashboard disagree:

1. Prefer the execution backend's observed terminal state for a finished job.
2. Preserve the failed record; append a correction/new event rather than
   mutating history.
3. Update the current snapshot only when the real outcome is known.
4. Re-render/export from that snapshot, then report any stale note that could
   not be refreshed.
5. If the backend result is indeterminate, use “unknown” and list the exact
   evidence gap. Never upgrade unknown to completed by intuition.

## Read-only inspector exit meanings

The bundled inspector exits `0` for a readable audit, even when it reports
warnings such as malformed JSON, stale state, missing files, or a failed
terminal state. It exits nonzero for invalid CLI arguments or an inaccessible
project/workspace root. Use `--format json` when another tool needs stable
fields; human-readable output is the default.
