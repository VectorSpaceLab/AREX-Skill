# EverOS Package Overview

## When to read

Read this for the repo-level mental model before choosing a sub-skill, or when a task spans setup, memory APIs, storage, and operations.

## Runtime identity

- Distribution and import root: `everos`.
- Python requirement: 3.12 or newer.
- Console script: `everos`.
- Base install includes CLI/TUI, FastAPI, Markdown/SQLite/LanceDB storage, provider facades, metrics, and core `everalgo-*` memory packages.
- Optional extras: `multimodal` for `everalgo-parser[svg]`; `otel` for OpenTelemetry SDK/exporter.

## Layer model

EverOS follows a single-direction layered architecture:

```text
entrypoints (cli/api) -> service -> memory -> infra
component/core/config are cross-cutting
```

The operating implication: future agents should use the public CLI and HTTP API for application work. Source-level imports such as internal repos, table managers, or writers are implementation evidence, not the ordinary user interface.

## Storage model

EverOS is Markdown-first:

| Store | Role | Rebuildable from Markdown? |
|---|---|---|
| Markdown under the memory root | Source of truth: user episodes/profiles, agent cases/skills, knowledge documents/topics | It is the truth |
| SQLite under `.index/sqlite/` | State, buffers, cascade queue, OME job store and audit | Mostly, except unprocessed buffers are not in Markdown yet |
| LanceDB under `.index/lancedb/` | Vector, BM25, scalar search indexes | Yes |

The default memory root is `~/.everos`; CLI flags and `EVEROS_ROOT` can point to another root.

## Capability tiers

| Capability | Required configuration | Notes |
|---|---|---|
| CLI help, `everos init`, `everos demo --plain`, no-lifespan OpenAPI schema | Base install | No provider credentials required. |
| Server startup and memory extraction | `[llm]` model/base_url/api_key | LLM is a startup-hard requirement in the normal FastAPI lifespan. |
| Keyword search over existing indexed rows | Base plus runtime data | Search service can degrade when vector providers are unavailable. |
| Vector/hybrid/agentic memory search, clustering, reflection, agent skill extraction | Embedding and sometimes rerank/LLM | Missing providers return capability/configuration errors on paths that require them. |
| Knowledge upload/search | Embedding + rerank, and LLM for extraction | Read/list/delete/metadata patch stay reachable when providers are missing. |
| Multimodal memory or non-text knowledge parsing | `everos[multimodal]` plus `[multimodal]`; Office also needs LibreOffice | Plain UTF-8 text uploads can bypass parser. |
| Tracing/Langfuse | `everos[otel]` plus `[observability]` | Off by default; content capture is opt-in. |

## Public surfaces

- CLI: `everos init`, `everos server start`, `everos config show`, `everos cascade ...`, `everos demo ...`.
- HTTP: `/health`, `/metrics`, `/api/v2/memory/add`, `/flush`, `/search`, `/get`, `/api/v2/knowledge/*`, `/api/v2/ome/trigger`.
- Generated skill helpers: each sub-skill bundles safe scripts that inspect the installed package or call a user-supplied running server.
