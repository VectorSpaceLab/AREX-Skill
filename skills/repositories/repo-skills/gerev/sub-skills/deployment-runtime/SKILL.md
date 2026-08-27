---
name: deployment-runtime
description: "Start Gerev from source or Docker, build the UI, and troubleshoot
  storage, boot, and deployment layout issues."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Gerev Deployment and Runtime

Use this sub-skill when the task is about running Gerev from source, starting the Docker/compose stack, building the UI bundle, or troubleshooting startup/storage/port behavior.

## Best-fit tasks

- Start Gerev locally from the backend source tree.
- Explain the Dockerfile, compose file, runtime ports, and storage mount.
- Build or serve the React UI bundle that the backend serves in production.
- Diagnose startup failures that happen before search or connector workflows can run.
- Understand where the backend stores SQLite, queue, Faiss, BM25, and telemetry files.

## Start here

1. Read [`deployment-runtime.md`](references/deployment-runtime.md) for the boot sequence, Docker/compose layout, storage paths, and UI build expectations.
2. Read [`troubleshooting.md`](references/troubleshooting.md) for startup, storage, model-cache, and UI-serving failures.
3. Read [`frontend-api.md`](../../references/frontend-api.md) when you need the backend route contract that the UI expects during boot and polling.
4. Run the bundled [`inspect_runtime_paths.py`](scripts/inspect_runtime_paths.py) read-only helper for a concise layout summary:

   ```bash
   python scripts/inspect_runtime_paths.py --app-dir <checkout>/app --json
   ```

   Add `--strict` when you want the helper to exit nonzero if required runtime files are missing.

## High-signal routing checks

- `run.sh` runs migrations and starts Uvicorn on port `80`.
- `Dockerfile` installs the backend dependencies, pre-caches the model stack, and copies the built UI into `/ui`.
- `docker-compose.yaml` mounts `~/.gerev/storage:/opt/storage` and shows the optional NVIDIA GPU reservation.
- `app/paths.py` selects `/opt/storage` in Docker-like mode and a home-directory storage tree otherwise.
- The current source tree has a known startup blocker in the search/index import chain: `split_PDF_into_paragraphs` is imported but missing.

## Boundaries

Included here: source startup, Docker/compose, UI build, storage layout, ports, and the boot-time service behavior that makes the app usable.

Do not use this sub-skill for connector credential setup or search ranking internals unless those details are needed only to explain startup/runtime behavior.
