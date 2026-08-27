---
name: telemetry-attempt-archive
description: "Use this quip-miner sub-skill for telemetry REST endpoints,
  snapshot aggregation, node health checks, and mining attempt/solution archive
  inspection by solution number."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# Telemetry and Attempt Archive

Use this sub-skill when the user needs to check a running miner's REST telemetry, diagnose stale snapshots, inspect per-solution mining attempts, or understand the solution archive layout.

## Route By Task

- **Telemetry REST API:** Read `references/telemetry-api.md` for `/health`, `/api/v1/status`, `/api/v1/stats`, `/api/v1/system`, `/api/v1/miner/survey`, block endpoints, and `/api/v1/solve` behavior.
- **Attempt archive:** Read `references/attempt-archive.md` for directory layout, `solution_number` semantics, `dispatch_id` warnings, query APIs, and REST query parameters.
- **Failures:** Read `references/troubleshooting.md` for `/health` vs stats 503, stale snapshots, missing descriptor/survey, chain endpoint errors, and archive lookup problems.
- **Health/summary helpers:** Use `scripts/quip_node_health_check.py` for endpoint checks and `scripts/attempt_archive_summary.py` for local archive inspection.

## Common Commands

```bash
python scripts/quip_node_health_check.py http://127.0.0.1:8086 --verbose
curl http://127.0.0.1:8086/api/v1/status
curl 'http://127.0.0.1:8086/api/v1/mining/attempts?solution_number=196&limit=100'
curl 'http://127.0.0.1:8086/api/v1/mining/solutions?solution_number=196'
python scripts/attempt_archive_summary.py --archive ~/.quip-miner/mining_attempts --solution-number 196
```

## Key Rules

- `/health` proves the telemetry process is live, not that miner snapshots are fresh.
- In supervisor/multi-backend mode, the telemetry aggregator reads per-mode snapshot files and merges counters, miners, and modes.
- Attempt archives are keyed by chain-global **solution number**, not block number and not `dispatch_id`.
- `dispatch_id` is process-local scheduler coordination and resets on restart. Never use it as a durable identity.
- In Docker, attempts default under `$QUIP_RUNTIME_DIR/mining_attempts`; otherwise under `~/.quip-miner/mining_attempts`; `QUIP_MINING_ATTEMPTS_DIR` overrides both.

## Boundaries

- Route config that enables telemetry (`rest_host`, `rest_port`, Docker bind) to `../config-supervisor-deployment/SKILL.md`.
- Route identity/descriptor construction to `../identity-wallet-bootstrap/SKILL.md`.
- Route proof-chain download, BQM dumps, and topology validation to `../topology-proof-validation/SKILL.md`.
