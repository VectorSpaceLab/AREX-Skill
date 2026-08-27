# PyCaret Package Overview

This repository is a monorepo around the PyCaret 4 Control Plane stack. The root skill routes by workflow; this reference gives the coarse surface map and the install shape for each surface.

## Surface map

| Surface | Main paths | What it owns | Primary sub-skill |
| --- | --- | --- | --- |
| Engine | `packages/engine/pycaret/` | OOP experiment classes, `pycaret.api`, typed results, event logging, persistence, model and metric registries | `sub-skills/engine-workflows/` |
| Control Plane backend | `services/api/pycaret_server/` | FastAPI app, CLI, auth, runs/trials, deployments, storage, LLM advisories, orchestration | `sub-skills/control-plane-api/` |
| Web UI | `apps/web/src/` | React/Vite routes, typed API client, auth store, dynamic forms, run/trial/deployment pages | `sub-skills/web-ui/` |
| Platform operations | `infra/`, Docker and runtime files | Compose, secrets, queues, workers, backups, storage, GPU routing | `sub-skills/platform-operations/` |
| Maintainer workflow | `docs/revamp/`, `scripts/`, test suites, contributor docs | release notes, tests, decisions, kill-list, docs, repository maintenance | `sub-skills/repo-development/` |

## Install matrix

Use the smallest surface that covers the user task.

```bash
# Engine-only workflows.
python -m pip install -e packages/engine[anomaly,timeseries,test]

# Control Plane backend workflows.
python -m pip install -e services/api[test]

# Web UI workflows.
cd apps/web && npm install

# Full-stack local editing.
python -m pip install -e packages/engine[anomaly,timeseries,test]
python -m pip install -e services/api[test]
cd apps/web && npm install
```

## Shared assumptions

- PyCaret 4 engine usage is OOP-only; the legacy module-level functional API is gone.
- The engine and the Control Plane backend are separate Python install targets in this monorepo.
- `RunConfig` is the shared contract across notebook, API, UI, and LLM-facing surfaces.
- LLM assistance is advisory only; deterministic engine or server code performs the action after user approval.
- The web UI uses a Node toolchain separate from the Python packages.

## Helpful bundled checks

- `scripts/check_pycaret_stack.py`: confirms the installed engine package, the backend package, the engine model registries, and a created FastAPI app.
- `sub-skills/engine-workflows/scripts/engine_smoke.py`: engine recipe smoke checks.
- `sub-skills/control-plane-api/scripts/server_smoke.py`: isolated backend bootstrap check.
- `sub-skills/web-ui/scripts/ui_static_check.sh`: frontend typecheck/lint/test/build wrapper.

Use this reference when you need a fast reminder of which surface owns a task before opening a sub-skill.
