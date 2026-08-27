---
name: runtime-service
description: "Run and debug the MineContext/OpenContext Python backend runtime,
  APIs, configuration, storage, capture, processing, generation, chat, and local
  smoke checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Runtime service

Use this sub-skill for MineContext/OpenContext backend runtime tasks: starting
`opencontext`, configuring model/storage/auth/prompt settings, uploading or
capturing context, calling FastAPI endpoints, debugging content generation,
chat/completion flows, monitoring, and deterministic local smoke checks.

Route Electron app builds, PyInstaller packaging, signing, helper binaries, and
frontend release tasks to [desktop-packaging](../desktop-packaging/SKILL.md).
For cross-component orientation read the root
[architecture](../../references/architecture.md); for install/import or
runtime-vs-packaging failures read the root
[troubleshooting guide](../../references/troubleshooting.md) before the
workflow-specific troubleshooting page here.

## Runtime entry checklist

1. Confirm the installed backend package imports and the CLI is present:

   ```bash
   python -c "import opencontext; print(opencontext.__version__)"
   opencontext --help
   ```

2. Start from a known `CONTEXT_PATH` if you need disposable local data:

   ```bash
   mkdir -p .minecontext-data
   CONTEXT_PATH="$PWD/.minecontext-data" opencontext start --config config/config.yaml --host 127.0.0.1 --port 1733
   ```

3. Check health before calling data routes:

   ```bash
   curl -s http://127.0.0.1:1733/health
   curl -s http://127.0.0.1:1733/api/health
   ```

4. If API authentication is enabled, send `X-API-Key: <key>` or `?api_key=<key>`
   on protected routes; never print or persist the key in notes.
5. Do not run screenshot, web-link, model-validation, generation, chat, or
   completion workflows until the user confirms screen/browser/network/model
   access and supplies non-secret credentials through config, environment, or the
   settings API.

## Reference map

- [references/api-reference.md](references/api-reference.md): read when calling
  HTTP routes, matching request bodies, interpreting response envelopes, or
  debugging route-family ownership.
- [references/configuration.md](references/configuration.md): read before
  editing YAML, `CONTEXT_PATH`, model settings, storage backends, prompt
  language/files, content-generation intervals, or API auth.
- [references/data-formats.md](references/data-formats.md): read when creating
  raw context payloads, interpreting processed contexts, selecting supported
  document formats, or mapping storage tables and context types.
- [references/workflows.md](references/workflows.md): read for concrete CLI/API
  workflows covering startup, uploads, screenshots, folder monitoring, web
  links, context search, generation, chat/completions, monitoring, and local
  smokes.
- [references/troubleshooting.md](references/troubleshooting.md): read when a
  runtime workflow fails after the first health/config checks.
- [scripts/smoke_folder_monitor.py](scripts/smoke_folder_monitor.py): run for a
  deterministic CPU-only folder-monitor create/update/delete check with mocked
  storage cleanup.
- [scripts/smoke_document_text.py](scripts/smoke_document_text.py): run for a
  CPU-only text-document processing smoke that builds an isolated temporary
  runtime config and does not require model credentials.

## What this sub-skill owns

- `opencontext start`, `opencontext --help`, `OpenContext.initialize()`, capture
  startup, FastAPI app state, and health checks.
- FastAPI route families for web pages, settings, context search, screenshots,
  document/web-link uploads, vault documents, generated content, monitoring,
  events, completions, context-agent chat, conversations, and messages.
- Runtime configuration: `config.yaml`, environment interpolation,
  `CONTEXT_PATH`, model settings, prompt YAML, user settings, API auth, storage,
  content-generation tasks, capture, and processing.
- Capture/processing/storage workflows for folders, documents, screenshots, web
  links, ChromaDB, Qdrant, SQLite, and supported data formats.
- User-facing generation and consumption flows: activities, tips, todos,
  reports, context-agent chat, streaming, message interruption, and intelligent
  completion.

## Boundaries and safety

- Do not document or depend on the original repository checkout for normal use;
  prefer installed `opencontext` plus bundled references/scripts.
- Do not include API keys, private model endpoints, local virtualenv paths,
  package install prefixes, or user data paths in generated notes.
- Treat API settings updates, database resets, prompt imports, browser capture,
  screenshot capture, and generation calls as user-data or credential-sensitive.
- Use [desktop-packaging](../desktop-packaging/SKILL.md) for executable/app
  packaging tasks; this sub-skill only covers the backend after it is installed
  or running.
