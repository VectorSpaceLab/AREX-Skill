---
name: ui-and-storage
description: "Routes UltraRAG UI, chat, knowledge-base, memory, and storage
  workflows backed by the Flask application."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# UI and Storage

Use this sub-skill when the task is about the UltraRAG web UI, local storage,
chat sessions, knowledge-base operations, or the case-study viewer.

## Typical triggers

- `ultrarag show ui` or `ultrarag show case`
- `ui/backend`, `create_app`, pipeline manager, auth, chat store, KB visibility
- chat sessions, background chats, export, or memory sync
- uploading, indexing, deleting, or inspecting KB files
- `ULTRARAG_UI_STORAGE_ROOT`, `ULTRARAG_FRONTEND_DIR`, or session timeout env vars
- Frontend build or asset serving questions

## What this sub-skill covers

- The Flask backend created by `ui/backend/app.py`.
- Storage layout and the SQLite-backed auth/chat/visibility stores.
- Knowledge-base CRUD, pipeline CRUD, background chat tasks, and memory sync.
- Frontend asset resolution and the case-study viewer data format.

## What stays elsewhere

- Pipeline YAML and orchestration belong in `sub-skills/pipelines/`.
- Server tool/prompt contracts and backend selection belong in
  `sub-skills/servers/`.

## Start here

- Read `references/ui-backend.md` for the route catalog and main Flask entry
  points.
- Read `references/storage-auth.md` for the storage tree, SQLite stores, and
  environment variables.
- Read `references/troubleshooting.md` when the UI, case-study viewer, or KB
  storage fails.
- Run `scripts/inspect_ui_backend.py` for a quick route and storage summary.

## Common user questions this sub-skill should answer

- How do I start the UI or case-study viewer?
- Which directories and environment variables control UI storage?
- How do chat sessions, KB files, and visibility mappings get stored?
- Why is `show ui` or `show case` failing on this machine?
- How do I inspect the Flask route set without reopening the source tree?

## Practical workflow

1. Confirm whether the user wants the UI server, the case-study viewer, or the
   storage back end.
2. Check the storage root and the frontend asset directory.
3. Use the route and storage references to pick the right fix.
4. If the issue is actually with pipeline semantics or a server backend, switch
   to the corresponding sub-skill.

## Helpful commands

```bash
ultrarag show ui --host 127.0.0.1 --port 5050
ultrarag show case --config_path output/memory_*.json
```

If the user is asking about chat logic inside the pipeline engine itself, go
back to the pipelines sub-skill instead of editing UI storage rules here.
