# MineContext architecture reference

## Purpose

Read this when you need to route a task across MineContext backend runtime,
context data flow, storage, generation, and desktop packaging. This is a
distilled operating map, not a full source-code inventory.

## High-level system

MineContext combines a Python backend named `opencontext` with an Electron
frontend. The Python side owns context capture, processing, storage,
consumption, APIs, and server startup. The desktop side owns windows, local UI,
packaging, and helper binaries.

```text
input sources -> capture manager -> processor manager -> storage
                 |                  |                  |
                 |                  |                  +-- SQLite documents
                 |                  |                  +-- ChromaDB/Qdrant vectors
                 |                  |
                 |                  +-- document/screenshot processors
                 |                  +-- chunking, extraction, merging
                 |
                 +-- screenshot, folder, vault, web-link capture

storage + prompts + model clients -> generation/completion/chat services
                                  -> FastAPI routes and web UI
                                  -> Electron desktop app
```

## Backend layers

| Layer | Main responsibility | Important surfaces |
| --- | --- | --- |
| CLI/server | Starts and hosts FastAPI | `opencontext start`, `OpenContext`, route modules, templates/static files |
| Configuration | Loads YAML, env substitutions, user settings, prompts | `${VAR}` and `${VAR:default}` interpolation, prompt language `zh`/`en`, user prompt overrides |
| Capture | Creates raw contexts | screenshot capture, folder monitor, vault monitor, web-link capture |
| Processing | Converts raw contexts into processed contexts | document processor, screenshot processor, chunkers, entity processor, context merger |
| Models/LLM | Calls chat and embedding providers | OpenAI-compatible clients and Doubao/Ark embedding path |
| Storage | Stores vectors and generated documents | ChromaDB or Qdrant vector backends, SQLite document backend |
| Consumption | Generates outputs from stored context | activities, smart tips, todos, daily/weekly reports, completions, context-agent chat |
| API/web | Exposes UI and machine endpoints | health, settings, contexts, generation, monitoring, chat, documents, screenshots, vaults |

## Context lifecycle

1. **Capture** converts a source into `RawContextProperties`. Common sources are
   screenshots, local files/folders, vault notes, web links, and direct input.
2. **Processing** checks source type and file format, then routes to document or
   screenshot processors. Text/structured documents can be processed locally;
   visual screenshots, scanned pages, and insight generation require a working
   model service.
3. **Extraction and classification** create `ProcessedContext` objects whose
   extracted data belongs to context types such as `entity_context`,
   `activity_context`, `intent_context`, `semantic_context`,
   `procedural_context`, `state_context`, or `knowledge_context`.
4. **Storage** upserts processed context to the vector backend and stores
   generated markdown/todos/activities/tips/conversations in SQLite tables.
5. **Consumption** retrieves context and generates activities, todos, tips,
   reports, completion suggestions, and chat responses.
6. **APIs and UI** expose these operations through FastAPI JSON endpoints,
   server-rendered web pages, and the Electron frontend.

## Configuration model

MineContext uses layered configuration:

1. Base YAML configuration.
2. Environment variable interpolation such as `${LLM_API_KEY}` or
   `${CONTEXT_PATH:.}`.
3. User settings saved by API/UI updates.
4. Runtime state inside managers and singletons.

If configuration or prompt state appears inconsistent, check the root
[troubleshooting](troubleshooting.md) page first, then the runtime-service
[configuration reference](../sub-skills/runtime-service/references/configuration.md).

## Desktop packaging boundary

The desktop app is not just a static web shell. Packaging normally has two
products:

1. a PyInstaller backend executable containing `opencontext/`, config files,
   web templates/static assets, hidden imports, and the runtime hook; and
2. an Electron app that copies the backend into `frontend/backend/`, includes
   platform resources, and on macOS packages Quartz-based helper binaries for
   window inspection/capture.

Use [desktop-packaging](../sub-skills/desktop-packaging/SKILL.md) for build and
helper-binary tasks. Use [runtime-service](../sub-skills/runtime-service/SKILL.md)
for backend APIs and behavior once the service is installed or running.
