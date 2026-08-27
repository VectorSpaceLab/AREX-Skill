---
name: cascade-and-evolution
description: "Use this sub-skill for EverOS Markdown storage layout, cascade
  sync/rebuild/backfill, OME strategies, reflection, and operational recovery."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# EverOS Cascade and Evolution

Use this sub-skill when a task asks about the memory-root layout, Markdown source of truth, SQLite/LanceDB indexes, `everos cascade` operations, OME strategy configuration, backfill, reflection, or operational recovery.

## Read/run map

- Read [storage and cascade](references/storage-and-cascade.md) for memory-root layout, Markdown/SQLite/LanceDB roles, cascade daemon loops, and CLI commands.
- Read [evolution and reflection](references/evolution-and-reflection.md) for OME strategy behavior, `ome.toml`, manual trigger, reflection, and backfill phases.
- Read [troubleshooting](references/troubleshooting.md) for schema drift, queue failures, rebuild safety, file descriptor exhaustion, watcher issues, provider gates, and server-lock conditions.
- Run [everos_status_probe.py](scripts/everos_status_probe.py) for safe `/health` and/or `everos cascade status` probes. It does not run destructive operations.

## Command safety

| Command | Safe with running server? | Notes |
|---|---|---|
| `everos cascade status` | yes | Read-only queue/LSN summary. |
| `everos cascade sync [PATH]` | yes | Drains pending queue; can force-enqueue one Markdown path. |
| `everos cascade fix` | yes | Lists failed rows. |
| `everos cascade fix --apply` | generally yes | Requeues retryable failures and drains once. |
| `everos cascade rebuild` | no | Stop server first; it drops/recreates LanceDB business tables. |
| `everos cascade backfill` | phases 2/3 need exclusive OME access | Uses providers and can spend model/embedding budget. |

## Key model

EverOS writes Markdown as truth, records durable queue/state in SQLite, and derives LanceDB rows asynchronously. If derived indexes are wrong, rebuild from Markdown; do not treat LanceDB as the canonical store.
