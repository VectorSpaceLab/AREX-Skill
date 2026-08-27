---
name: minecontext
description: "Guides MineContext/OpenContext runtime service, context workflows,
  configuration, and desktop packaging tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MineContext repo skill

Use this skill for the MineContext repository and its Python backend package,
whose installed distribution is `MineContext`, import package is `opencontext`,
and console entry point is `opencontext`.

MineContext is a local-first context-aware AI partner. Its backend captures
screen, document, vault, and web-link context; processes that material into
context types; stores it with SQLite plus ChromaDB or Qdrant; and exposes
FastAPI routes, web pages, content-generation jobs, and chat/completion flows.
The repo also contains an Electron/React desktop app that bundles the Python
backend through PyInstaller.

## When to use this skill

Use this skill when the task asks to:

- start or debug the `opencontext` server or CLI;
- configure model endpoints, API keys, storage, prompts, content-generation
  intervals, or API authentication;
- ingest screenshots, documents, folders, vault notes, or web links;
- query or troubleshoot MineContext context search, generated activities,
  todos, tips, reports, chat, completions, or monitoring;
- build the PyInstaller backend executable or Electron desktop app;
- understand the repo's backend/frontend architecture enough to make a focused
  code or packaging change.

Do not use this skill for unrelated context-management libraries, generic
FastAPI guidance without MineContext-specific APIs, or ordinary Electron apps
that do not bundle the `opencontext` backend.

## First checks

1. Confirm that the current task really names MineContext, OpenContext,
   `opencontext`, or one of its repo-specific surfaces such as screenshot
   capture, local context storage, generated todos/tips/reports, or the
   Electron package.
2. If a checkout is present and freshness matters, read
   [references/repo-provenance.md](references/repo-provenance.md). Refresh this
   skill when the commit, dirty state, package version, or major public paths
   differ from that snapshot.
3. Verify the installed backend before trusting runtime advice:

   ```bash
   python -m pip install -e .
   python -c "import opencontext; print(opencontext.__version__)"
   opencontext --help
   ```

   The bundled [scripts/check_runtime.py](scripts/check_runtime.py) performs a
   broader import and CLI smoke check without starting the server.
4. If the task requires model inference, screenshot analysis, web-link capture,
   or generated insights, confirm whether the user has a working
   OpenAI-compatible or Doubao endpoint. Many workflows import offline but need
   credentials or a local model server for real generation.

## Route map

| Task shape | Read next | Why |
| --- | --- | --- |
| Start the backend, inspect `opencontext start`, configure models/auth/storage, upload context, call API routes, or debug runtime behavior | [runtime-service](sub-skills/runtime-service/SKILL.md) | Owns CLI, FastAPI, capture, processing, storage, context generation, and bundled runtime smokes. |
| Build the backend executable, package the Electron app, diagnose `pnpm`, PyInstaller, helper binaries, signing, or platform packaging | [desktop-packaging](sub-skills/desktop-packaging/SKILL.md) | Owns backend/desktop build flow and macOS helper binary guidance. |
| Understand system layers, data flow, and component boundaries before routing | [references/architecture.md](references/architecture.md) | Condensed architecture from the repo's own overview and source layout. |
| A failure crosses install/import/config/runtime/build boundaries | [references/troubleshooting.md](references/troubleshooting.md) | Cross-cutting recovery before following a workflow-specific troubleshooting page. |
| Updating the managed repo-skill router entry after verification | [references/repo-routing-metadata.json](references/repo-routing-metadata.json) | Structured metadata consumed by the repo-skill importer. |

## Repository facts to preserve

- Public branding: **MineContext**.
- Python distribution: `MineContext`.
- Python import package: `opencontext`.
- Console command: `opencontext`.
- Primary server class: `opencontext.server.opencontext.OpenContext`.
- Default server command: `opencontext start`.
- Default service port in config and docs: `1733` for the user-facing backend
  debugger, while `opencontext.cli` falls back to configured web settings.
- Default local storage is rooted under `${CONTEXT_PATH:.}` and includes SQLite
  document storage plus ChromaDB vector collections unless config switches to
  Qdrant.
- Frontend packaging uses `frontend/package.json`, `electron-builder.yml`, and
  a prebuilt PyInstaller backend copied into `frontend/backend/`.

## Safe operating rules

- Do not put API keys, `CONTEXT_PATH` values, local virtualenv paths, or user
  data paths in generated artifacts or public notes.
- Do not run screenshot, VLM, embedding, web-link, or regeneration flows unless
  the user has supplied credentials, a local model endpoint, and permission for
  any network/browser work.
- Prefer bundled smoke scripts over original repo examples when checking this
  skill. The original examples were used as evidence; the skill-owned scripts
  are the reusable helpers.
- Treat packaging and release commands as mutating operations. Run the
  desktop-packaging preflight first and ask before deleting build outputs,
  installing toolchains, or using signing credentials.
