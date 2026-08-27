# Watchdog and Research Wiki

## Research Wiki

Initialize with the ARIS Research Wiki workflow in the target project. The expected structure includes:

```text
research-wiki/
  index.md
  log.md
  gap_map.md
  query_pack.md
  papers/
  ideas/
  experiments/
  claims/
  graph/edges.jsonl
```

The helper exposes commands for initialization, slug generation, paper ingestion, claim/idea/experiment updates, graph edges, index rebuilds, query-pack rebuilds, stats, logs, and synchronization. Keep helper resolution explicit; do not assume a top-level `tools/` exists in a project-local installation.

## Watchdog Task Schema

A task registration needs a stable `name`, a task `type` such as `training` or `download`, and a `session`. `session_type` defaults to `screen` and can be `tmux`. Training tasks may include a GPU list; download tasks may include a target path. Registration is deduplicated by name and writes task/status files under the watchdog base directory.

Use the official watchdog command from the user's ARIS checkout only after deciding the monitoring scope. The generated skill does not start the daemon or mutate remote servers.

## Status Semantics

- Session liveness indicates whether a `screen`/`tmux` session still exists.
- GPU utilization is an observation, not proof that a training run is correct.
- Download status uses file/path evidence and should distinguish active, stale, complete, and missing states.
- Unregister completed tasks and keep alerts/status files available for diagnosis.

## Experiment Operations

Use the experiment queue for bounded multi-seed/config sweeps with crash-safe state, wave gating, stale-session cleanup, and OOM retry policies. Keep remote SSH, Vast, Modal, and GPU environments explicit in project configuration and verify them before launch.
