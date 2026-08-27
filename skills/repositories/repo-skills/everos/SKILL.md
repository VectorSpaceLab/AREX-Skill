---
name: everos
description: "Use this skill for EverOS local-first Markdown memory service
  setup, HTTP memory and knowledge APIs, cascade/OME operations, and
  observability integration."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# EverOS Repo Skill

EverOS is a Python 3.12+ local-first memory runtime for AI agents and user chats. It stores source-of-truth memory as Markdown, uses SQLite for system state and queues, and projects searchable rows into LanceDB for BM25/vector/scalar retrieval.

Use this skill when the task involves installing EverOS, configuring a memory root, running the server, calling the memory or knowledge HTTP APIs, operating cascade/OME maintenance, or enabling tracing/metrics.

## Quick route map

| User intent | Read next |
|---|---|
| Install EverOS, create config files, inspect health, start the server, or run the demo | [setup-and-config](sub-skills/setup-and-config/SKILL.md) |
| Add/flush/search/get user or agent memory through `/api/v2/memory/*`, work with prompt slots or multimodal message content | [memory-api](sub-skills/memory-api/SKILL.md) |
| Upload, replace, patch, delete, list, or search knowledge documents and topics | [knowledge-base](sub-skills/knowledge-base/SKILL.md) |
| Understand Markdown/SQLite/LanceDB layout, run `everos cascade`, rebuild indexes, configure OME, trigger reflection | [cascade-and-evolution](sub-skills/cascade-and-evolution/SKILL.md) |
| Configure structured logs, Prometheus `/metrics`, OpenTelemetry, Langfuse tracing, content-capture privacy, or request-id correlation | [observability](sub-skills/observability/SKILL.md) |

## Minimal public setup

```bash
python -m pip install everos
# optional extras:
python -m pip install 'everos[multimodal]'
python -m pip install 'everos[otel]'

everos init --root ~/.everos
$EDITOR ~/.everos/everos.toml
everos server start --root ~/.everos
curl http://127.0.0.1:8000/health
```

EverOS has no in-process public client mode for ordinary app use: start the service and call the HTTP API. The `everos` console script is the primary local operator surface.

## Configuration capabilities

Base install supports CLI, config generation, FastAPI app construction, Markdown/SQLite/LanceDB runtime, keyword-oriented inspection, and deterministic demo preview. Real memory extraction requires an OpenAI-compatible LLM configured in `[llm]`. Vector/hybrid/agentic search, knowledge search, clustering, and some OME strategies require embedding and/or rerank providers. Multimodal content requires the `multimodal` extra plus `[multimodal]` provider settings; Office document parsing also needs LibreOffice on the server host. OpenTelemetry export requires the `otel` extra and `[observability]` settings.

## Shared references

- [Repository provenance](references/repo-provenance.md) records the source snapshot, package version, and evidence paths. Read it before deciding whether this skill is stale for a checkout.
- [Package overview](references/package-overview.md) summarizes architecture, runtime surfaces, storage model, and capability tiers.
- [Cross-cutting troubleshooting](references/troubleshooting.md) covers install/import, provider gates, config/root confusion, security, and eventual consistency issues that span sub-skills.

## Safe helpers

Prefer sub-skill-owned scripts for focused tasks. The helpers are safe by default: they only inspect local imports, print schema/config information, or call a user-supplied running server. Any helper that writes memory or knowledge requires an explicit flag.

## Important operating boundaries

- New integrations should use `/api/v2`; `/api/v1` is a legacy alias.
- EverOS binds to `127.0.0.1:8000` by default and ships no built-in authentication. Put an authenticated gateway in front before exposing it beyond loopback.
- Markdown is the source of truth. SQLite and LanceDB are derived/rebuildable, but deleting all of `.index/` also deletes buffered messages not yet extracted.
- `/add` and `/flush` write Markdown synchronously when extraction occurs, but LanceDB search is eventually consistent. Use retry/backoff or `everos cascade sync` when a deterministic local drain is needed.
- Do not claim live LLM, embedding, rerank, multimodal, or Langfuse behavior is verified unless the target environment has credentials and the relevant optional dependencies configured.
