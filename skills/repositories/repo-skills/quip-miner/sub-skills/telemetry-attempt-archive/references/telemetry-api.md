# Telemetry REST API

The telemetry process is an aiohttp server that exposes a success/error envelope:

```json
{"success": true, "data": {}, "timestamp": 1234567890}
```

Errors use `success: false`, `error`, and `code` fields.

## Endpoint Map

| Method/path | Purpose | Notes |
| --- | --- | --- |
| `GET /health` | Liveness probe | Always returns an ok success envelope if the telemetry process is alive. |
| `GET /` | Endpoint directory | Lists public endpoints and version. |
| `GET /api/v1/status` | Miner identity/status plus optional chain head fields | Reads snapshot and best-effort chain data. Includes `is_mining`, `last_successful_submission`, `consecutive_submit_failures`, `runtime_incompatible`, `sync_state`, and per-mode breakdown. |
| `GET /api/v1/stats` | Raw merged stats snapshot | 503 when no snapshot is available/fresh enough. |
| `GET /api/v1/system` | Descriptor from snapshot | 503 when descriptor is absent. |
| `GET /api/v1/miner/survey` | Stable miner survey payload | Prefer this for stable dashboard shape when present. |
| `GET /api/v1/block/latest` | Latest chain block payload | Requires validator client. |
| `GET /api/v1/block/{number}` | Block payload by height | Requires validator client. |
| `GET /api/v1/block/{number}/header` | Header + hash by height | Requires validator client. |
| `POST /api/v1/solve` | Disabled direct solve service | Returns 503 `SOLVE_DISABLED`; deploy a dedicated solve service for direct sampling. |
| `GET /api/v1/mining/attempts` | Attempt records | Query by `solution_number` or `miner_id` + `solution_number`. |
| `GET /api/v1/mining/solutions` | Stored top-5 spin configs | Query by `solution_number`, optional `miner_id`. |

## Snapshot Modes

Legacy mode reads a single stats snapshot file. Aggregator mode reads every `telemetry-stats-*.json` file in a snapshot directory, merges controller counters by summing, unions miner lists by id, and keeps a `modes` breakdown.

A missing or corrupt snapshot is normal during startup and returns 503/stale rather than crashing the telemetry process.

## Status Interpretation

- `is_mining`: inferred from snapshot file mtime freshness, not a direct worker heartbeat.
- `last_successful_submission`: epoch seconds for the last landed proof; `None` with active mining can mean the node is mining but not winning.
- `consecutive_submit_failures` and `runtime_incompatible`: diagnose nodes that mine but cannot land proofs.
- `sync_state`: pool sync-wait progress, `None` when healthy.
- `modes`: per-backend group breakdown in aggregator mode.

## Chain-backed Endpoint Caveat

The telemetry process owns its own validator client. Snapshot endpoints can work while chain-backed block endpoints fail due to validator connectivity or sync issues. Treat 502/503 from block endpoints separately from `/health` and `/api/v1/stats`.
