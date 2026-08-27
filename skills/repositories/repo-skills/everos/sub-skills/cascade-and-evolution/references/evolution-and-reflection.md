# Evolution and Reflection Reference

## OME role

The Offline Memory Engine runs asynchronous strategies after memory cells are produced. Strategies write derived Markdown such as atomic facts, foresights, profiles, agent cases, agent skills, and reflection outputs.

`ome.toml` lives under the memory root and hot-reloads strategy overrides. Use it to enable/disable strategies, tune cron, idle windows, counters, and retries.

## Strategy families

| Family | Examples | Provider expectations |
|---|---|---|
| Always registered LLM-oriented strategies | atomic facts, foresight, agent cases, user profile | Need LLM when executed. |
| Embedding-dependent strategies | skill clustering, agent skill extraction, profile clustering, reflection | Body-guard when embedding is unavailable. |

Tier changes require server restart for provider capability singletons to rebuild.

## Manual trigger

HTTP route:

```bash
POST /api/v2/ome/trigger
{"name":"reflect_episodes","timeout":120,"force":true}
```

Response status:

| Status | Meaning |
|---|---|
| `ok` | At least one strategy dispatched and runs settled within timeout. |
| `timeout` | Dispatched, but engine did not go idle before timeout. |
| `not_dispatched` | Strategy was rejected by enabled/routing/counter gates; use `force=true` only when appropriate. |

A trigger response reflects strategy run state, not necessarily LanceDB index convergence. Check cascade health after writes.

## Reflection

Reflection consolidates clustered episodes into a single chronological narrative. It is disabled by default. Enable in `ome.toml`:

```toml
[strategies.reflect_episodes]
enabled = true
```

Default schedule is weekly. Running too often can degrade memory because the merge is lossy. Reflection writes a merged episode with `parent_type: cluster`, deprecates original episodes/facts, and records audit state.

## Backfill

`everos cascade backfill` is a tier-upgrade operation:

1. `vectors`: embed older memory rows.
2. `clusters`: create/update clusters.
3. `skills`: extract agent skills from case clusters.

It may spend embedding/LLM budget. Phase 2/3 require exclusive OME jobstore access; stop the server when prompted. Exit codes distinguish success, user abort, provider failure, server-running lock, partial row failures, and interrupt.
