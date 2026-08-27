---
name: memory-api
description: "Use this sub-skill for EverOS HTTP memory add, flush, search, get,
  multimodal content, prompt slots, and memory API troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# EverOS Memory API

Use this sub-skill for application-level memory workflows through the EverOS HTTP API: adding conversations, flushing session buffers, searching user or agent memory, listing memory rows, handling multimodal content, and tuning prompt slots.

## Read/run map

- Read [API reference](references/api-reference.md) for request/response shapes, owner scoping, filter DSL, search methods, and error envelopes.
- Read [workflows](references/workflows.md) for add/flush/search loops, live demo-equivalent calls, prompt slots, and multimodal payload patterns.
- Read [troubleshooting](references/troubleshooting.md) for provider gates, validation errors, eventual consistency, search misses, and multimodal failures.
- Run [memory_http_smoke.py](scripts/memory_http_smoke.py) against a running server. It defaults to `/health`; add `--add-flush-search` only when writes are intended.
- Run [dump_everos_openapi.py](scripts/dump_everos_openapi.py) to inspect the installed package OpenAPI schema without starting a server.

## Core endpoints

Use `/api/v2` for new integrations:

| Endpoint | Purpose |
|---|---|
| `POST /api/v2/memory/add` | Add one or more messages to a session buffer; may extract if a boundary trips. |
| `POST /api/v2/memory/flush` | Force extraction of the current session tail. |
| `POST /api/v2/memory/search` | Ranked retrieval over user episodes/profiles or agent cases/skills. |
| `POST /api/v2/memory/get` | Paginated listing over one memory type. |

`/api/v1` is a compatibility alias with the same handlers.

## Minimal add/flush/search loop

```bash
TS=$(($(date +%s) * 1000))
BASE=http://127.0.0.1:8000

curl -s -X POST "$BASE/api/v2/memory/add" \
  -H 'Content-Type: application/json' \
  -d "{\"session_id\":\"demo-001\",\"messages\":[{\"sender_id\":\"alice\",\"role\":\"user\",\"timestamp\":$TS,\"content\":\"I love climbing in Yosemite every spring.\"}]}"

curl -s -X POST "$BASE/api/v2/memory/flush" \
  -H 'Content-Type: application/json' \
  -d '{"session_id":"demo-001"}'

curl -s -X POST "$BASE/api/v2/memory/search" \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"alice","query":"Where do I like to climb?","method":"hybrid","top_k":5}'
```

## Key decisions

- `messages[].timestamp` should be Unix epoch milliseconds.
- `sender_id` becomes the user owner for user-role messages and is path-validated.
- Exactly one of `user_id` or `agent_id` is required for `/search` and `/get`.
- Use `app_id` and `project_id` to isolate tenants/projects; defaults are `default`.
- Search can be eventually consistent after writes because LanceDB projection is asynchronous.
- Multimodal content items require explicit parser/provider setup; plain string content is safest.
