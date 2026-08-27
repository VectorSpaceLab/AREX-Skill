---
name: simulation-run
description: "Starts, monitors, stops, inspects, interviews, and finalizes
  MiroFish OASIS simulation runs across parallel, Twitter, Reddit, IPC, and
  optional Zep graph-memory modes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# simulation-run

Use this sub-skill when a task asks to start a prepared MiroFish simulation, choose `parallel`/`twitter`/`reddit`, poll run status, inspect timelines/actions/posts/comments/stats, interview agents, close the interactive environment, stop a process, or reason about graph-memory update finalization.

## Route first

- If the request is about building or resetting the Zep graph, route to the sibling `graph-build` sub-skill.
- If the request is about creating a simulation, generating profiles, or producing `simulation_config.json`, route to the sibling `simulation-setup` sub-skill.
- If the run has reached a terminal successful or stopped state and the user asks for an analysis/report, route to the sibling `reporting` sub-skill after confirming graph-memory finalization is not still pending.

## Read or run the bundled material

- Read [references/workflows.md](references/workflows.md) for start modes, monitor loops, stop versus close-env decisions, interviews, graph-memory finalization, and report handoff.
- Read [references/api-reference.md](references/api-reference.md) when constructing backend API calls, interpreting response fields, or diagnosing status codes.
- Read [references/runtime-artifacts.md](references/runtime-artifacts.md) when inspecting `state.json`, `run_state.json`, platform `actions.jsonl`, SQLite platform databases, logs, or IPC directories.
- Read [references/troubleshooting.md](references/troubleshooting.md) when a start/stop/restart/interview/memory-update operation fails, hangs, or returns a pending barrier.
- Run `python scripts/action_logger.py --help` to inspect the bundled JSONL helper, or `python scripts/action_logger.py --self-test` to verify the helper writes and reads the MiroFish action-log shape without starting OASIS.

## Minimal safe operating loop

1. Confirm the backend is reachable and you have a `simulation_id` whose preparation is complete.
2. Start with `POST /api/simulation/start` using a real JSON boolean for `force` and `enable_graph_memory_update` when present.
3. Poll `GET /api/simulation/<simulation_id>/run-status` for lightweight progress; use detail/actions/timeline endpoints only when you need event data.
4. Use `POST /api/simulation/env-status` before any interview. Interviews require a live wait-mode environment.
5. Prefer `POST /api/simulation/close-env` for a completed interactive environment; use `POST /api/simulation/stop` for running, stuck, or abort-required processes.
6. Treat `stopping` as a non-terminal graph-ingestion barrier. Do not generate reports until it resolves to `completed` or `stopped`; investigate or retry if it resolves to `failed`.
