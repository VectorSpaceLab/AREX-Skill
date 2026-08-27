# Simulation-run workflows

This reference covers runtime control after a simulation has already been created and prepared. It does not cover graph construction, entity filtering, profile generation, or simulation-configuration generation except as preconditions.

## Preconditions

Have these before starting a run:

- A reachable Flask backend with the simulation blueprint mounted under `/api/simulation`.
- A `simulation_id` already known to the backend.
- Preparation completed: `state.json` exists for the simulation, preparation metadata says `config_generated: true`, and the runtime directory contains `simulation_config.json`, `reddit_profiles.json`, and `twitter_profiles.csv`.
- Required runtime services and credentials are configured for the selected behavior: OASIS dependencies and LLM credentials for simulation, and `ZEP_API_KEY` only when using graph-memory updates.
- A platform decision:
  - `parallel`: run both Twitter and Reddit worlds together. This is the default API mode.
  - `twitter`: run only the Twitter launcher.
  - `reddit`: run only the Reddit launcher.

If the graph is missing or stale, use `graph-build`. If profiles or config are missing, use `simulation-setup`.

## Start by backend API

Use the API for normal operation because the backend owns run-state persistence, process cleanup, graph-memory update barriers, and polling endpoints.

```bash
curl -sS -X POST "$BASE_URL/api/simulation/start" \
  -H 'Content-Type: application/json' \
  -d '{
        "simulation_id": "sim_xxx",
        "platform": "parallel",
        "max_rounds": 5,
        "enable_graph_memory_update": false,
        "force": false
      }'
```

Key rules:

- `platform` must be `parallel`, `twitter`, or `reddit`; omitted means `parallel`.
- `max_rounds`, when supplied, is coerced to a positive integer and truncates the LLM-generated schedule.
- `force` and `enable_graph_memory_update` must be JSON booleans, not strings such as `"false"`.
- `force: true` first finalizes any active or incomplete old run, then clears prior run artifacts, but preserves config/profile files.
- If the old run is still finalizing graph ingestion, start returns a pending/conflict response; do not clean logs or restart until finalization resolves.

A successful start returns a `SimulationRunState` shape with `runner_status`, `process_pid`, platform running flags, timestamps, total rounds, and the `graph_memory_update_enabled`/`force_restarted` flags.

## Long OASIS launcher modes

The backend maps start modes to long-running OASIS launchers. Keep these launchers reference-only in this skill: they own external OASIS processes, import third-party packages, read runtime environment variables, and may keep an interactive environment alive.

Launcher behavior to know when debugging backend logs:

| Launcher behavior | Runtime command shape | Notes |
| --- | --- | --- |
| Parallel default | `python <backend-launcher> --config simulation_config.json` | Runs both platforms concurrently and writes separate platform action logs. Use the backend-managed launcher download for the chosen mode. |
| Parallel, one platform only | `python <backend-launcher> --config simulation_config.json --twitter-only` or `--reddit-only` | Useful when reproducing a backend `platform` decision manually. |
| Single Twitter | `python <backend-launcher> --config simulation_config.json` | Twitter-only environment, action set, and database. |
| Single Reddit | `python <backend-launcher> --config simulation_config.json` | Reddit-only environment, action set, and database. |
| Bounded run | Add `--max-rounds N` | Mirrors API `max_rounds`; useful for truncating expensive schedules. |
| No interactive wait | Add `--no-wait` | The environment closes immediately after the simulation loop; interviews will not be available. |

The backend launches scripts from its own scripts directory with the simulation directory as the working directory, redirects stdout/stderr to `simulation.log`, and sets UTF-8 process environment variables.

## Monitor loop

Use a lightweight poll by default:

```bash
while true; do
  curl -sS "$BASE_URL/api/simulation/$SIM_ID/run-status"
  sleep 3
done
```

Interpretation:

- `idle`: no `run_state.json` has been saved yet.
- `starting`: the backend has claimed the simulation but has not fully published process resources.
- `running`/`paused`: simulation is active or wait-mode is active.
- `stopping`: non-terminal finalization barrier; wait or diagnose, do not report.
- `completed`: the process ended naturally and any graph-memory drain succeeded.
- `stopped`: a manual stop finalized safely.
- `failed`: process, monitor, configuration, or graph-memory finalization failed.

Use deeper endpoints only when needed:

- `GET /api/simulation/<simulation_id>/run-status/detail` returns the run state plus all action records and current-round `recent_actions`.
- `GET /api/simulation/<simulation_id>/actions?limit=100&offset=0&platform=twitter&agent_id=1&round_num=3` is the paginated action-reader endpoint.
- `GET /api/simulation/<simulation_id>/timeline?start_round=0&end_round=10` groups actions by round.
- `GET /api/simulation/<simulation_id>/agent-stats` ranks agents by activity and action distribution.
- `GET /api/simulation/<simulation_id>/posts` and `/comments` inspect platform SQLite tables after the OASIS launcher has created them.

Platform `simulation_end` events in `actions.jsonl` set `twitter_completed` or `reddit_completed`, but they are not terminal success by themselves. The monitor still waits for process exit and optional graph-memory drain before publishing `completed` or `stopped`.

## Stop versus close-env

Choose carefully:

| Need | API | Effect |
| --- | --- | --- |
| Abort a running/stuck simulation or finalization | `POST /api/simulation/stop` | Terminates the process tree, lets the monitor read final action-log tail, drains graph-memory updates if enabled, then publishes `stopped` or `failed`. |
| Gracefully leave wait-mode after the simulation loop completed | `POST /api/simulation/close-env` | Sends an IPC `close_env` command to the live environment; the launcher exits cleanly and the simulation metadata is set to completed. |
| Check if interviews/close-env are possible | `POST /api/simulation/env-status` | Reads `env_status.json`; true means commands can be accepted. |

`/stop` may return `202` with `pending: true` when the monitor still owns bounded finalization. Keep polling `run-status`. If it later becomes `failed` with an ingestion error, retry `/stop`; the updater is retained so a safe drain can be attempted again without replaying ambiguous writes.

## Interview flow

Interviews are IPC commands handled by the launcher after OASIS has a live environment. They are not available if the launcher was run with `--no-wait`, if `close-env` already ran, or if the process crashed.

1. Check liveness:

   ```bash
   curl -sS -X POST "$BASE_URL/api/simulation/env-status" \
     -H 'Content-Type: application/json' \
     -d '{"simulation_id":"sim_xxx"}'
   ```

2. Interview one agent:

   ```bash
   curl -sS -X POST "$BASE_URL/api/simulation/interview" \
     -H 'Content-Type: application/json' \
     -d '{"simulation_id":"sim_xxx","agent_id":0,"prompt":"What changed your opinion?","platform":"twitter","timeout":60}'
   ```

3. Batch interview:

   ```bash
   curl -sS -X POST "$BASE_URL/api/simulation/interview/batch" \
     -H 'Content-Type: application/json' \
     -d '{"simulation_id":"sim_xxx","interviews":[{"agent_id":0,"prompt":"Why did you post?"},{"agent_id":1,"prompt":"Who influenced you?","platform":"reddit"}],"timeout":120}'
   ```

4. Read history with `POST /api/simulation/interview/history` using optional `platform`, `agent_id`, and `limit` filters.

When no platform is supplied in a dual-platform run, MiroFish attempts both platforms and returns a per-platform result map. The backend prepends an interview prefix to discourage the agent from calling tools and to request a direct text answer.

## Graph-memory update flow

Set `enable_graph_memory_update: true` only when you want simulated activities to become Zep graph episodes.

Start-time safeguards:

- The project graph ID is authoritative; a stale graph copied into an older simulation is rejected.
- Start uses a graph lifecycle lock so graph reset/delete and simulation memory writes cannot cross.
- If a report is actively reading the same graph, start with memory updates returns a conflict until reporting finishes.

During a run:

- The monitor reads per-platform `actions.jsonl` and sends successful, meaningful action records to `ZepGraphMemoryUpdater`.
- Event rows and failed actions are not ingested. `DO_NOTHING` is skipped.
- Activities are grouped by platform into bounded text episodes with provenance metadata such as simulation ID, platform, rounds, agent IDs, and action types.

Finalization:

- On natural completion, manual stop, or backend shutdown, the producer is terminated first, the action-log tail is read, then the updater drains queued/buffered activities and waits for Zep Cloud episode processing.
- While draining, `runner_status` is `stopping`; this blocks report generation and graph deletion.
- Non-idempotent write failures are surfaced instead of replayed. The retained updater keeps the run retryable and keeps graph lifecycle guards aware of incomplete ingestion.

## Report handoff

Hand off to `reporting` only when:

- `runner_status` is `completed` or `stopped`.
- `runner_status` is not `stopping`.
- No graph-memory failure remains in `error`.
- If memory update was enabled, ingestion has drained successfully or the user explicitly accepts a report without dynamic graph-memory updates.

For `failed` runs, first inspect `simulation.log`, `run_state.json`, and graph-memory finalization errors, then decide whether to retry stop, force restart, or rerun preparation.
