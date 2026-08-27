# Memory API Workflows

## First write and recall

1. Start a configured server.
2. `POST /api/v2/memory/add` with a session and messages.
3. At conversation end, `POST /api/v2/memory/flush`.
4. Retry `/api/v2/memory/search` with backoff until cascade catches up.
5. Use `/api/v2/memory/get` when you need deterministic listing instead of ranking.

The bundled `scripts/memory_http_smoke.py --add-flush-search` performs this public HTTP flow against a running server.

## User vs agent memory

- User memory: search with `user_id`; results include episodes, atomic facts nested under episodes, and optional profile.
- Agent memory: search with `agent_id`; results include agent cases and agent skills.
- `app_id` and `project_id` isolate both tracks.

## Search method choice

| Method | Use when | Provider expectations |
|---|---|---|
| `keyword` | Need lexical/BM25 search or provider-light debugging | Works on indexed keyword tokens. |
| `vector` | Need semantic nearest-neighbor recall | Requires embedding vectors. |
| `hybrid` | Default best general search | Uses sparse+dense fusion; rerank behavior depends on route. |
| `agentic` | Need cluster-aware/agentic retrieval behavior | Requires richer provider setup. |

If a method returns provider errors, retry with `keyword` only if keyword behavior is acceptable for the task; do not pretend it validates vector behavior.

## Prompt slots

EverOS currently ships bundled prompt slot files for `boundary_detection` and `episode_extract`. The loader returns a template only when a slot YAML has `enabled: true` and a non-empty `template`; otherwise EverOS passes `None` through to the algorithm default. App-level and per-call overlays are planned, so do not promise deployment-level prompt override beyond the currently shipped defaults unless the target version confirms it.

## Multimodal message workflow

1. Install `everos[multimodal]`.
2. Configure `[multimodal]` model, base URL, and API key.
3. For Office documents, install LibreOffice on the server host.
4. Send `messages[].content` as a list of content items.
5. Expect only parsed text to flow into downstream memory; raw asset bytes are not persisted as memory content.

Prefer `file://` only for files reachable by the server process and configure allowlisted directories when exposing the API beyond loopback.

## OpenAPI inspection

Use the bundled OpenAPI helper when you need current route/schema names from the installed package without booting the full lifespan:

```bash
python sub-skills/memory-api/scripts/dump_everos_openapi.py --summary
```
