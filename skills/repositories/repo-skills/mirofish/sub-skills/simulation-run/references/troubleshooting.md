# Simulation-run troubleshooting

Use this reference when runtime control fails or behavior looks inconsistent. Prefer API status plus runtime artifacts before rerunning expensive OASIS simulations.

## Quick triage order

1. `GET /api/simulation/<simulation_id>`: confirm the simulation exists and is prepared.
2. `GET /api/simulation/<simulation_id>/run-status`: identify `runner_status`, counts, and `error`.
3. Inspect `run_state.json` and `simulation.log` for backend-restart or process-exit context.
4. Inspect platform `actions.jsonl` files when status counters or timelines disagree.
5. If graph-memory updates were enabled, treat `stopping` as a protected ingestion barrier and do not report or delete the graph until it resolves.

## Failure matrix

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Start returns missing simulation ID or simulation not found | Wrong `simulation_id` or backend data root | List simulations for the project, then retry with the returned ID. |
| Start returns not ready or missing config | Preparation did not complete or required files are absent | Route to `simulation-setup`; verify `state.json`, `simulation_config.json`, `reddit_profiles.json`, and `twitter_profiles.csv`. |
| Start returns `max_rounds` invalid | Non-integer or non-positive `max_rounds` | Send a positive integer or omit the field. |
| Start returns `force must be a JSON boolean` or `enable_graph_memory_update must be a JSON boolean` | Caller sent string booleans | Send `true`/`false` as JSON booleans, not `"true"`/`"false"`. |
| Start returns invalid platform | Platform not in `parallel`, `twitter`, `reddit` | Pick one of the supported values. |
| Start says the simulation is already running or ending | Existing `run_state.json`, in-memory process, or retained updater is active | Poll status. If active and you need to abort, call `/stop`; if terminal and you need a fresh run, use `force: true`. |
| `force: true` returns conflict/pending | Old graph-memory finalization still owns the run | Do not delete logs or restart. Poll `run-status`; retry start only after `stopped`/`completed`, or retry `/stop` if finalization becomes `failed`. |
| `run-status` is `idle` after a start failure | Start failed before publishing `run_state.json` or it was cleaned | Check the start response, `simulation.log`, and required launcher/config files. |
| `run-status` is `starting` for too long | Process spawn or monitor publication failed | Inspect `simulation.log` and backend logs. A monitor-start failure should terminate the spawned process and save `failed`. |
| `run-status` is `failed` with a process exit code | OASIS/LLM/dependency/config/runtime exception | Read the tail of `simulation.log`; fix credentials/dependencies/config or rerun with a small `max_rounds`. |
| Platform completed flags are true but `runner_status` is still running/stopping | Platform action logs ended before process and updater finalization completed | Wait for process exit and graph-memory drain. Do not report yet. |
| Action counts stop increasing while process is running | OASIS may be in a quiet round, logs are not yet flushed, or monitor has not tailed the file | Poll again, inspect `simulation.log`, and check raw platform `actions.jsonl`. |
| Timeline/actions miss platform values | Raw per-platform JSONL omits `platform` by design | Use API readers; they infer platform from `twitter/` or `reddit/` directories. |
| Posts/comments endpoint returns empty data | Platform DB does not exist yet, table not created, or chosen platform has no posts/comments | Wait for actions, use correct `platform`, and inspect action logs before assuming failure. |
| Interview returns environment not running | Launcher was run with `--no-wait`, `close-env` was already called, process crashed, or simulation loop has not entered wait-mode | Check `/env-status`, `env_status.json`, and `simulation.log`. Start/run without `--no-wait` if interviews are required. |
| Interview times out | IPC response did not appear before timeout or OASIS is busy | Increase timeout, check `ipc_commands/` and `ipc_responses/`, check `simulation.log`, then retry a smaller batch. |
| Batch interview returns partial or no results | Some agent IDs are invalid for the selected platform or platform is unavailable | Verify `agent_configs` IDs in `simulation_config.json`, platform availability, and use item-level `platform` only when needed. |
| `close-env` says already closed | `env_status.json` is absent or not `alive` | Treat as harmless if no more interviews are needed; otherwise restart in wait-mode. |
| `close-env` times out but reports success | The close command may have been accepted while the environment was shutting down | Poll `env-status` and `run-status`; confirm `env_status.json` becomes stopped or process exits. |
| `/stop` returns `202` with `pending: true` | Monitor is inside bounded final action-log tail read and/or Zep Cloud drain | Keep polling; do not mark failed or force restart while pending. |
| `/stop` later fails with `Zep图谱写入未完整完成` or ingestion incomplete | Graph-memory updater failed or timed out while draining | Retry `/stop`; the retained updater preserves retry state. Do not replay ambiguous graph writes manually. |
| Graph reset/delete is blocked by an active simulation/updater | A simulation still owns or drains the graph | Stop/finalize the simulation first. Only explicit graph destruction should discard an inactive failed updater. |
| Start with memory update returns stale graph or graph changed | Simulation references an older graph than the current project | Re-prepare the simulation after graph rebuild/reset before enabling memory updates. |
| Start with memory update reports active reports | A report is reading the graph | Wait for report generation to finish, then retry. |
| Zep Cloud validation is requested | Manual live validation requires credentials/network and may create/delete or retain a cloud graph | Do not run it as an automatic smoke check. Ask for explicit authorization and retention/cleanup preference. |

## Stop and finalization recovery

When a user asks to stop:

1. Call `POST /api/simulation/stop`.
2. If it succeeds, verify `runner_status: stopped`.
3. If it returns `pending: true`, preserve `stopping`, poll, and explain that graph-memory finalization is still bounded and monitor-owned.
4. If it fails with graph-ingestion incomplete, call `/stop` again only after checking the updater remains retained. Do not force cleanup before a safe drain.
5. If stop fails for a process-termination reason, inspect `simulation.log`, backend logs, and `process_pid`; avoid manually deleting runtime files unless the process is confirmed gone and the user accepts losing runtime evidence.

Shutdown cleanup follows producer-before-consumer ordering: terminate the OASIS process, let the monitor read final action-log tail, then drain graph-memory updates. If cleanup fails, state remains retryable instead of silently discarding an updater.

## Graph-memory updater details that affect diagnosis

- Successful activities are batched by platform, with batch size 5 by default.
- Failed action records and `DO_NOTHING` are skipped.
- Each Cloud episode is capped to a safe text size and records metadata for simulation ID, platform, rounds, agent IDs, and action types.
- Graph writes are not automatically replayed after ambiguous failure because `graph.add` has no idempotency key. A failed batch is surfaced and finalization fails closed.
- Episode processing is polled with a deadline. Timeout leaves the run in `failed`/retryable state with the updater retained.

## Runtime artifact checks

Use these checks without running repo-native tests/examples:

```bash
# Validate that a run-state file is parseable JSON.
python -m json.tool "<simulation_data_dir>/<simulation_id>/run_state.json" >/dev/null

# Count raw platform action rows.
wc -l "<simulation_data_dir>/<simulation_id>/twitter/actions.jsonl" \
      "<simulation_data_dir>/<simulation_id>/reddit/actions.jsonl"

# Smoke-test the bundled action logger helper in a temp directory.
python scripts/action_logger.py --self-test
```

If action-log JSON parsing fails, inspect the last partial line first; it may have been read while the launcher was appending.

## Live cloud validation caveat

The standalone Zep Cloud validation workflow is manual/reference-only. It needs live credentials and network access, exercises Cloud graph and batch APIs, and has retention logic for incomplete updater drains. Do not run it during routine skill validation or a simulation-run triage unless the user explicitly authorizes live Cloud side effects and confirms whether a test graph may be deleted or retained.
