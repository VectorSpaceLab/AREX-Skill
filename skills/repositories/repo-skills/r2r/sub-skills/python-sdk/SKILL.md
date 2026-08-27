---
name: python-sdk
description: "Use the R2R Python sync and async clients for auth, method groups,
  pagination, downloads, and response handling."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Python SDK

Use this sub-skill when the user wants to call R2R from Python with `R2RClient` or `R2RAsyncClient`.

## What it owns

- client construction and base URL setup
- API key, login token, and project-name handling
- sync vs async method differences
- wrapped results, pagination, downloads, exports, and streaming
- method-group routing to ingestion, retrieval, graph, and server topics

## Start here

```python
from r2r import R2RClient

client = R2RClient(base_url="http://localhost:7272")
print(client.system.health().results)
```

## Key conventions

- Choose **one** auth path: API key or login token.
- `client.users.login(email, password)` stores the access token on the client.
- `client.set_api_key(...)` sets API-key auth.
- `client.set_project_name(...)` adds the `x-project-name` header.
- `R2RResults.results` unwraps a typed response.
- `PaginatedR2RResult.results` holds the page items and `total_entries` holds the count.

## Route out when the question is domain-specific

- Ingestion, chunking, metadata, or filters: `../ingestion-documents/SKILL.md`
- Search, RAG, or streaming citations: `../retrieval-rag/SKILL.md`
- Graph extraction or graph CRUD: `../graph-workflows/SKILL.md`
- Server install/config/Docker: `../server-configuration/SKILL.md`
- JavaScript client: `../javascript-sdk/SKILL.md`

## Bundled assets

- `references/api-reference.md`
- `references/workflows.md`
- `references/troubleshooting.md`
- `scripts/python_sdk_smoke.py`
