# Telemetry and Archive Troubleshooting

## `/health` passes but `/api/v1/stats` is 503

The HTTP process is alive, but no readable snapshot is available yet. Causes:

- Miner child is still starting.
- Snapshot file was removed on graceful child shutdown.
- Aggregator snapshot directory is wrong or empty.
- Snapshot file is stale/corrupt and skipped.

Check the supervisor config, snapshot directory, and child logs. In Docker, verify the shared runtime volume.

## `/api/v1/system` or `/api/v1/miner/survey` is 503

The snapshot exists but lacks `descriptor` or `miner_survey`. This may happen during early startup, older builds, or descriptor-builder failures. Use `/api/v1/status` and logs to distinguish.

## Chain block endpoints fail

`/api/v1/block/*` requires the telemetry process's validator client. Snapshot endpoints can still work. Check validator URLs, sync state, and network connectivity.

## `is_mining` false while process is running

`is_mining` is inferred from snapshot freshness. A stuck or stopped child may leave a stale file; the aggregator uses max-age gating to avoid phantom miners. Check child process liveness and snapshot mtime.

## No attempts for a solution

Verify:

- You used `solution_number`, not block number or `dispatch_id`.
- The archive root matches `QUIP_MINING_ATTEMPTS_DIR` or `QUIP_RUNTIME_DIR` used by the miner.
- A submission exists for broad `solution_number` queries; otherwise the REST broad query returns 404.
- For miner-specific queries, the `miner_id` is filename-safe and exactly matches the archive file.

## Stale archive after restart

If the solution number did not change, writing into the same directory is correct. The solution number tracks the logical round. A different solution number gets a different directory.
