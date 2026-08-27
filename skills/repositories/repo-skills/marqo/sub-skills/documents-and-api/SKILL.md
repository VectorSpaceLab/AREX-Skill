---
name: documents-and-api
description: "Public Marqo HTTP API routes, document workflows, typeahead calls,
  route-level validation, and safe smoke checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# documents-and-api

Use this sub-skill when a task is about Marqo's public HTTP surface: service health, index CRUD from the API boundary, document add/update/read/delete calls, embed and recommend route mechanics, typeahead routes, API request/response models, validation triage, and safe HTTP smoke previews.

## Start here

- Route map and request/error model summary: [references/api-routes.md](references/api-routes.md)
- Document, embed, recommend, and minimal search-route validation workflows: [references/document-workflows.md](references/document-workflows.md)
- Typeahead request models and workflows: [references/typeahead.md](references/typeahead.md)
- Error and failure triage: [references/troubleshooting.md](references/troubleshooting.md)
- Safe request preview / optional live smoke script: [scripts/marqo_http_smoke.py](scripts/marqo_http_smoke.py)

## Scope

Covered here:

- `GET /`, `GET /health`, index list/create/settings/stats/health/delete routes.
- Document routes for add-or-replace, partial update, get one, get batch, and delete batch.
- Route-level mechanics for `embed`, `recommend`, and the minimal public `search` request-shape checks needed to triage validation failures.
- Typeahead suggestions, query indexing, query lookup/delete, and stats.
- FastAPI/Pydantic validation behavior, Marqo error envelopes, count headers, and route gates.
- Dry-run HTTP smoke generation that is network-free unless `--send` is explicitly used.

Route elsewhere:

- Deep index schema, Vespa application package behavior, and schema update internals -> `index-and-vespa`.
- Search ranking semantics, filters, facets, score modifiers, hybrid/lexical/tensor ranking, sort, collapse, and relevance tuning -> `search-and-ranking`.
- Model registry internals, inference orchestration, Triton/model-management services, and backend acceleration -> `inference-and-models`.
- Local service startup, Docker/compose, Vespa/Triton process management, and native test command selection -> `local-development`.

## Operating pattern

1. Identify the route family and confirm whether it is public or route-gated.
2. Use the bundled references for request body shape, aliases, response fields, and validation pitfalls.
3. Before touching a live service, run the smoke script with `--print-only` or no mode flag to inspect the exact HTTP methods, paths, and JSON bodies.
4. Use `--send` only when a Marqo API service is intentionally running and the caller accepts that the smoke sequence creates, mutates, and deletes the named index.
5. For validation failures, inspect whether the response is a FastAPI 422 `detail` response or a Marqo error envelope with `message`, `code`, `type`, and `link`.
