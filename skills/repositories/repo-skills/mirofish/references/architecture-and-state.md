# Architecture and state model

## Component map

MiroFish has three cooperating layers:

1. **Frontend**: Vue/Vite routes for the five-step workflow. It calls backend APIs through axios modules and displays graph, setup, simulation, report, and interaction state.
2. **Backend API**: Flask blueprints under `/api/graph`, `/api/simulation`, and `/api/report` plus `/health`.
3. **Backend services**: Python services for parsing files, generating ontology/config/profile/report content with LLMs, building and reading Zep Cloud graphs, running OASIS simulations, IPC/interviews, graph-memory update finalization, and report-side graph tools.

The source package is named `mirofish-backend`; its import package is `app`.

## Service families

| Family | Main responsibilities | Skill owner |
| --- | --- | --- |
| Graph parsing/building | upload files, extract text, generate ontology, configure Zep schema, ingest chunks, read graph nodes/edges, reset/delete graphs | `graph-build` |
| Simulation setup | create simulation records, read graph entities, filter labels, generate OASIS profiles, generate `simulation_config.json`, expose realtime setup artifacts | `simulation-setup` |
| Simulation runtime | start OASIS launcher processes, track run state, expose timelines/actions/posts/comments/stats, handle interviews and environment IPC, drain graph-memory updates | `simulation-run` |
| Reporting | plan sections, run Report Agent with graph tools, stream logs/progress, serve sections/full report, chat with completed report context | `reporting` |
| Cross-cutting utilities | configuration validation, locale-aware messages, OpenAI-compatible request shaping, Zep client lifecycle, logging | root |

## High-level state transitions

```text
project created
  -> ontology_generated
  -> graph_building
  -> graph_completed
  -> simulation created
  -> simulation preparing
  -> simulation ready
  -> simulation running
  -> simulation stopping / finalizing graph-memory updates
  -> simulation completed or stopped
  -> report generating
  -> report completed
  -> report interaction unlocked
```

A failed step generally preserves enough metadata for inspection and recovery. Do not assume a later step can repair an earlier failed state; route back to the owning sub-skill and recover there.

## Local artifact areas

Backend-generated artifacts live under the backend upload tree during normal operation:

- Uploaded source files and extracted project metadata.
- Simulation directories containing state, profiles, config, run state, logs, action streams, IPC files, and optional platform databases.
- Report directories containing progress, outline, sections, full report, agent log, console log, and metadata.

These artifact directories are runtime data, not source files. Inspect them using the nearest sub-skill reference before modifying or deleting them.

## Frontend route mental model

The frontend mirrors the public workflow:

- Home/process graph pages: project creation, upload, ontology, graph build, graph visualization.
- Environment setup view: simulation creation, profile/config generation, setup status, downloads.
- Simulation run view: runtime status, actions, timeline, stats, posts/comments, close/stop/interview affordances.
- Report view: report generation, progress, sections, logs, download/delete.
- Interaction view: Report Agent chat and graph tool interactions.

When a user describes UI behavior, map it to the owning API family rather than searching the frontend first. Use frontend evidence mainly for public names, default button behavior, and polling expectations.

## API namespaces

| Namespace | Purpose | Owning sub-skill |
| --- | --- | --- |
| `GET /health` | backend health | root |
| `/api/graph/*` | project, ontology, graph build, task polling, graph data, reset/delete | `graph-build` |
| `/api/simulation/*` setup endpoints | create, prepare, prepare status, entities, profiles, config, download setup artifacts | `simulation-setup` |
| `/api/simulation/*` runtime endpoints | start, stop, close-env, run-status/detail, timelines/actions/posts/comments/stats, interview, IPC/env status | `simulation-run` |
| `/api/report/*` | report generation/status/progress/sections/logs/download/delete/chat/tools | `reporting` |

## Concurrency and lifecycle rules

- A graph cannot be reset or deleted safely while build, simulation, memory update, or report consumers are active.
- Simulation stop can enter a `stopping` state while graph-memory updates drain; this blocks reporting and graph deletion until terminal.
- Report generation checks that the simulation has reached a terminal state and that graph-memory updates are not active.
- `close-env` and `stop` are distinct: use close-env for an interactive environment that is done but not necessarily an active process kill; use stop for running, stuck, or abort-required simulations.

## Backend verification stance

The selected skill scope is service/API orchestration and CPU-checkable behavior. The repo may run on a host with GPU-capable Torch, but this skill does not require GPU evidence. Live Zep Cloud validation is intentionally manual because credentials and cloud graph deletion/retention behavior are involved.
