# Simulation runtime API reference

All paths below are mounted under the Flask backend. Replace `<simulation_id>` with the actual ID and send/receive JSON unless noted.

## Precondition and inspection endpoints

| Endpoint | Method | Inputs | Response data | Notes |
| --- | --- | --- | --- | --- |
| `/api/simulation/<simulation_id>` | GET | path ID | `SimulationState`; includes `run_instructions` when status is `ready` | Use to confirm a simulation exists and is prepared enough to run. |
| `/api/simulation/list` | GET | optional `project_id` query | array of simulations and `count` | Useful when user only knows a project. |
| `/api/simulation/<simulation_id>/profiles` | GET | optional `platform=twitter|reddit` | `platform`, `count`, `profiles` | Omitting platform uses the simulation's default platform: Reddit when both are enabled, otherwise the enabled platform. |
| `/api/simulation/<simulation_id>/config` | GET | path ID | generated `simulation_config.json` content | Configuration generation belongs to `simulation-setup`; this endpoint is safe for runtime inspection. |

## Start and stop control

### `POST /api/simulation/start`

Request body:

```json
{
  "simulation_id": "sim_xxx",
  "platform": "parallel",
  "max_rounds": 5,
  "enable_graph_memory_update": false,
  "force": false
}
```

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `simulation_id` | string | yes | Prepared simulation to run. |
| `platform` | string | no | `parallel`, `twitter`, or `reddit`; default `parallel`. |
| `max_rounds` | integer-like | no | Positive cap on the computed simulation rounds. Invalid or non-positive values return `400`. |
| `enable_graph_memory_update` | JSON boolean | no | When true, successful agent activities are batched into Zep graph episodes. String booleans are rejected. |
| `force` | JSON boolean | no | Stop/finalize a prior active run and clean old run artifacts before restarting. String booleans are rejected. |

Success response `data` is `SimulationRunState` plus:

- `max_rounds_applied` when `max_rounds` was supplied.
- `graph_memory_update_enabled`.
- `force_restarted`.
- `graph_id` when graph-memory updates were enabled.

Important failures:

- `400` missing simulation ID, invalid platform, invalid max rounds, unprepared simulation, missing graph ID for graph memory, or string booleans.
- `409` when a previous run cannot be safely restarted yet, a graph changed during start, a stale simulation graph would be used for memory updates, or a report is actively reading the graph.
- `409` with `pending: true` means old graph-memory finalization is still draining; do not clean/restart yet.

### `POST /api/simulation/stop`

Request body:

```json
{"simulation_id": "sim_xxx"}
```

Success returns `data` as `SimulationRunState` with `runner_status: stopped`. `202` with `success: false` and `pending: true` means stop was requested but the monitor still owns finalization. Keep polling. A `500` can mark the simulation failed if safe termination or graph-memory drain fails.

### `POST /api/simulation/env-status`

Request body:

```json
{"simulation_id": "sim_xxx"}
```

Response `data` fields:

- `simulation_id`.
- `env_alive`: true only when `env_status.json` says `alive`.
- `twitter_available` and `reddit_available`: detailed availability for parallel wait-mode when written by the launcher; single-platform wait-mode may omit these and the backend reports false defaults.
- `message`: human-readable availability text.

### `POST /api/simulation/close-env`

Request body:

```json
{"simulation_id": "sim_xxx", "timeout": 30}
```

Sends an IPC `close_env` command. Use after the simulation loop finishes and the environment is waiting for commands. Success can also mean the environment was already closed or the close command was sent but response timed out while shutdown was in progress. The simulation metadata is set to `completed` when the API succeeds.

## Status and event endpoints

| Endpoint | Method | Query/body | Main fields | Notes |
| --- | --- | --- | --- | --- |
| `/api/simulation/<simulation_id>/run-status` | GET | none | `runner_status`, round counts, platform flags, action counts, timestamps, `process_pid`, `error` | Lightweight polling endpoint. Returns `idle` defaults when no run state exists. |
| `/api/simulation/<simulation_id>/run-status/detail` | GET | optional `platform=twitter|reddit` | run state plus `all_actions`, `twitter_actions`, `reddit_actions`, `recent_actions`, `rounds_count` | Reads full action history; avoid tight polling on large runs. |
| `/api/simulation/<simulation_id>/actions` | GET | `limit`, `offset`, `platform`, `agent_id`, `round_num` | `count`, `actions` | Paginates action records after filtering. |
| `/api/simulation/<simulation_id>/timeline` | GET | `start_round`, `end_round` | `rounds_count`, `timeline` | Groups actions by round and platform. |
| `/api/simulation/<simulation_id>/agent-stats` | GET | none | `agents_count`, `stats` | Counts per-agent total, platform split, action types, first/last times. |
| `/api/simulation/<simulation_id>/posts` | GET | `platform`, `limit`, `offset` | `platform`, `total`, `count`, `posts` | Reads the platform SQLite `post` table. Missing DB/table returns success with empty data. |
| `/api/simulation/<simulation_id>/comments` | GET | `platform`, `post_id`, `limit`, `offset` | `count`, `comments` | Reads the platform SQLite `comment` table. Missing DB/table returns success with empty data. |

## Interview endpoints

Interviews require `env-status.env_alive: true`.

| Endpoint | Method | Body | Behavior |
| --- | --- | --- | --- |
| `/api/simulation/interview` | POST | `simulation_id`, `agent_id`, `prompt`, optional `platform`, optional `timeout` | Sends one `interview` IPC command. No platform in a dual run means both available platforms are interviewed. |
| `/api/simulation/interview/batch` | POST | `simulation_id`, `interviews`, optional default `platform`, optional `timeout` | Each interview item needs `agent_id` and `prompt`; item-level `platform` overrides the default. |
| `/api/simulation/interview/all` | POST | `simulation_id`, `prompt`, optional `platform`, optional `timeout` | Builds one interview for every `agent_id` in `simulation_config.json`. |
| `/api/simulation/interview/history` | POST | `simulation_id`, optional `platform`, optional `agent_id`, optional `limit` | Reads `trace` rows whose action is `interview` from platform databases. |

The backend rewrites interview prompts by prepending a direct-answer instruction if it is not already present. Returned responses contain `success`, command metadata, and either result details or `error`. A timeout yields an HTTP timeout response for the user-facing API.

## Runtime data shapes

### `SimulationState.status`

`created`, `preparing`, `ready`, `running`, `stopping`, `paused`, `stopped`, `completed`, `failed`.

`ready` means the simulation is prepared. `running`, `stopping`, `stopped`, `completed`, and `failed` mean preparation had already succeeded earlier.

### `SimulationRunState.runner_status`

`idle`, `starting`, `running`, `paused`, `stopping`, `stopped`, `completed`, `failed`.

Do not treat `twitter_completed` or `reddit_completed` alone as terminal success. They only reflect platform `simulation_end` action-log events.

### Action record

Backend action readers expose records like:

```json
{
  "round_num": 3,
  "timestamp": "2026-08-11T12:00:00",
  "platform": "twitter",
  "agent_id": 7,
  "agent_name": "Alice",
  "action_type": "CREATE_POST",
  "action_args": {"content": "..."},
  "result": null,
  "success": true
}
```

Per-platform JSONL action logs store `round` instead of `round_num` and usually omit `platform`; the backend injects platform based on the directory.

### Common action types

Twitter actions include `CREATE_POST`, `LIKE_POST`, `REPOST`, `FOLLOW`, `DO_NOTHING`, and `QUOTE_POST`.

Reddit actions include `LIKE_POST`, `DISLIKE_POST`, `CREATE_POST`, `CREATE_COMMENT`, `LIKE_COMMENT`, `DISLIKE_COMMENT`, `SEARCH_POSTS`, `SEARCH_USER`, `TREND`, `REFRESH`, `DO_NOTHING`, `FOLLOW`, and `MUTE`.

Interview is a manual IPC action and is read from platform `trace` tables for history.
