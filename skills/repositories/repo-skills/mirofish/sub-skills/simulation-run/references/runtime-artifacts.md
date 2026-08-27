# Simulation runtime artifacts

MiroFish stores each prepared/run simulation in a directory under the backend simulation-data root. Use the abstract layout below instead of relying on machine-specific checkout paths:

```text
<simulation_data_dir>/
  <simulation_id>/
    state.json
    simulation_config.json
    reddit_profiles.json
    twitter_profiles.csv
    run_state.json
    simulation.log
    env_status.json
    twitter/
      actions.jsonl
    reddit/
      actions.jsonl
    twitter_simulation.db
    reddit_simulation.db
    ipc_commands/
      <command_id>.json
    ipc_responses/
      <command_id>.json
    log/
      ... optional OASIS/library logs ...
```

The exact simulation-data root is controlled by the backend config, but all runtime APIs reason in terms of `<simulation_id>`.

## `state.json`

This is the simulation metadata projection managed by `SimulationManager`. Important fields:

| Field | Meaning |
| --- | --- |
| `simulation_id`, `project_id`, `graph_id` | Identity and graph association. The project graph is authoritative for graph-memory starts. |
| `enable_twitter`, `enable_reddit` | Platform enablement from simulation creation. |
| `status` | `created`, `preparing`, `ready`, `running`, `stopping`, `paused`, `stopped`, `completed`, or `failed`. |
| `entities_count`, `profiles_count`, `entity_types` | Preparation summary. |
| `profiles_generated`, `config_generated`, `config_reasoning` | Preparation artifacts and LLM reasoning state. |
| `current_round`, `twitter_status`, `reddit_status` | Coarse runtime projections. |
| `created_at`, `updated_at`, `error` | Timestamps and failure message. |

Preparation is considered usable for starting when `config_generated: true`, required config/profile files exist, and the status is one of the prepared statuses accepted by the backend.

## `simulation_config.json`

This file drives OASIS. Runtime code reads:

- `time_config.total_simulation_hours`.
- `time_config.minutes_per_round`.
- `agent_configs`, including each `agent_id` for interview-all.
- Event and platform-specific configuration generated earlier by `simulation-setup`.

The backend computes `total_rounds = total_simulation_hours * 60 / minutes_per_round`, then applies any API/CLI `max_rounds` cap.

## Profile files

- `twitter_profiles.csv` is the Twitter profile format expected by the launcher.
- `reddit_profiles.json` is the Reddit profile format expected by the launcher.

Even if only one platform will run, the backend's readiness check expects the prepared runtime directory to contain both standard files.

## `run_state.json`

This is the authoritative runtime state persisted by `SimulationRunner`. It mirrors the `SimulationRunState` response:

| Field group | Fields |
| --- | --- |
| Status | `runner_status`, `error`, `process_pid` |
| Round progress | `current_round`, `total_rounds`, `simulated_hours`, `total_simulation_hours`, `progress_percent` |
| Per-platform progress | `twitter_current_round`, `reddit_current_round`, `twitter_simulated_hours`, `reddit_simulated_hours` |
| Per-platform state | `twitter_running`, `reddit_running`, `twitter_completed`, `reddit_completed` |
| Counts | `twitter_actions_count`, `reddit_actions_count`, `total_actions_count` |
| Timestamps | `started_at`, `updated_at`, `completed_at` |
| Recent detail | `recent_actions`, `rounds_count` |

`run-status` reads this file when no in-memory state is available, so it is the first file to inspect after a backend restart.

## Platform `actions.jsonl`

Each platform directory has an append-only JSONL log. Event rows have an `event_type`; action rows have agent/action fields.

Event examples:

```json
{"event_type":"simulation_start","platform":"twitter","total_rounds":144,"agents_count":20}
{"event_type":"round_start","round":1,"simulated_hour":0}
{"event_type":"round_end","round":1,"actions_count":12,"simulated_hours":1}
{"event_type":"simulation_end","platform":"twitter","total_rounds":5,"total_actions":63}
```

Action example:

```json
{"round":2,"timestamp":"2026-08-11T12:00:00","agent_id":3,"agent_name":"Alice","action_type":"CREATE_POST","action_args":{"content":"..."},"result":null,"success":true}
```

Important details:

- Per-platform logs usually omit `platform`; the backend assigns `twitter` or `reddit` from the containing directory.
- Legacy single-file `actions.jsonl` can still be read if no per-platform logs exist.
- Event rows are skipped by action readers and graph-memory ingestion.
- Failed action rows (`success: false`) are skipped by graph-memory ingestion.
- `DO_NOTHING` is skipped by graph-memory ingestion even though it may appear in logs.
- A platform `simulation_end` event sets the platform completed flag, but terminal success waits for process exit and optional graph-memory drain.

The bundled `scripts/action_logger.py` can generate compatible JSONL fixtures for smoke checks without starting OASIS.

## `simulation.log`

The backend redirects launcher stdout/stderr here. Inspect this when:

- Start succeeded but `runner_status` becomes `failed`.
- The monitor reports a non-zero process exit.
- OASIS, LLM credentials, encoding, or dependency errors are suspected.
- IPC wait-mode did not become alive after the loop completed.

The launcher also may create library logs under `log/`; treat those as secondary evidence after `simulation.log` and `run_state.json`.

## Platform SQLite databases

The launchers create per-platform SQLite databases such as:

- `twitter_simulation.db`.
- `reddit_simulation.db`.

Runtime API readers use these tables when present:

| API | Table | Behavior if missing |
| --- | --- | --- |
| `/posts` | `post` | Success with empty posts and sometimes a message that the database does not exist. |
| `/comments` | `comment` | Success with empty comments. |
| `/interview/history` | `trace` rows where `action = 'interview'` | Empty history if DB/table/rows are absent. |

Do not assume every OASIS run creates posts/comments before the first few rounds. Use action logs as the primary live-observation source.

## IPC directories and env status

Interactive commands use file-system IPC:

```text
ipc_commands/<command_id>.json
ipc_responses/<command_id>.json
env_status.json
```

Command shape:

```json
{
  "command_id": "uuid",
  "command_type": "interview",
  "args": {"agent_id": 0, "prompt": "...", "platform": "twitter"},
  "timestamp": "..."
}
```

Allowed command types are `interview`, `batch_interview`, and `close_env`.

Response shape:

```json
{
  "command_id": "uuid",
  "status": "completed",
  "result": {"agent_id": 0, "response": "..."},
  "error": null,
  "timestamp": "..."
}
```

The client normally deletes both command and response files after receiving a valid response. If a command times out, the command file is removed by the client, but a late response may still be useful forensic evidence.

`env_status.json` contains at least:

```json
{"status":"alive","timestamp":"..."}
```

Parallel wait-mode also includes `twitter_available` and `reddit_available`. Single-platform wait-mode may not include those platform flags even though the environment is alive.

## Force restart cleanup scope

When `force: true` is accepted, the backend cleanup removes prior runtime artifacts:

- `run_state.json`.
- `simulation.log`.
- `stdout.log` and `stderr.log` if present.
- `twitter/actions.jsonl` and `reddit/actions.jsonl`.
- `twitter_simulation.db` and `reddit_simulation.db`.
- `env_status.json`.

It does not remove `simulation_config.json`, `twitter_profiles.csv`, or `reddit_profiles.json`. Cleanup does not run while old graph-memory finalization is still pending.
