---
name: platform-actions
description: "Document OASIS platform actions, platform settings, recommendation
  behavior, SQLite schema, trace behavior, group/interview/report/product
  workflows, and DB diagnostics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Platform Actions

Use this sub-skill when you need to choose the correct `ManualAction` for OASIS platform behavior, understand the `Platform` constructor and default presets, read or summarize the SQLite database, or debug why a platform action did not land in the expected table or trace row.

## Route elsewhere

- Agent or profile creation flows -> `agent-profiles`
- Full simulation lifecycle, step orchestration, and run control -> `simulation-workflows`
- Visualization and legacy result analysis -> `experiments-analysis`

## What this sub-skill covers

- `ActionType` values and the built-in Twitter/Reddit default action sets
- Exact `ManualAction.action_args` keys for platform, comment, group, report, product, search, trend, refresh, and interview actions
- `Platform.__init__` configuration, default platform presets, `Channel`, `Clock`, and `RecsysType`
- SQLite tables, trace payloads, and recommendation-table behavior
- Action-specific failure modes and DB inspection with [`scripts/oasis_db_summary.py`](scripts/oasis_db_summary.py)

## Operating flow

1. Start in [`references/action-reference.md`](references/action-reference.md) to pick the action type and its argument names.
2. Use [`references/platform-and-recsys.md`](references/platform-and-recsys.md) to confirm the platform preset, recsys type, channel, clock, and self-rating settings.
3. Use [`references/database-and-traces.md`](references/database-and-traces.md) to map the action to the SQLite tables and trace payload.
4. If the action failed or returned an empty result, use [`references/troubleshooting.md`](references/troubleshooting.md).
5. Inspect a live DB with [`scripts/oasis_db_summary.py`](scripts/oasis_db_summary.py) before guessing at schema or trace state.

## Notes

- `INTERVIEW` is usually a manual or harness-driven action; keep it out of LLM `available_actions` unless you intentionally want the model to choose it.
- `SIGNUP`, `UPDATE_REC_TABLE`, and `EXIT` are infrastructure-level actions. This sub-skill only routes them; it does not cover agent/profile creation or full environment lifecycle.
- When a post id belongs to a repost or quote, several actions resolve to the root post internally. See the action reference before debugging duplicate or missing-post errors.
