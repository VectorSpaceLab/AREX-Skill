---
name: elasticsearch-py
description: "Guide the official Elasticsearch Python client for cluster
  connections, generated APIs, async code, bulk ingestion, query DSL, ES|QL,
  optional integrations, and runtime troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Elasticsearch Python client

Use this skill when a task uses the official `elasticsearch` Python package or
asks for Elasticsearch connections, indexing/search APIs, async client code,
bulk helpers, the high-level DSL, ES|QL, vector-store helpers, or client
troubleshooting. The source snapshot is package version 9.5.0; read
[repo-provenance.md](references/repo-provenance.md) before deciding whether the
skill is stale for a different client checkout or version.

## Route the request

- **Connect, authenticate, configure transport, use generated API namespaces,
  or manage sync/async lifecycle:** read
  [client-operations](sub-skills/client-operations/SKILL.md).
- **Bulk index/update/delete, streaming, scan, reindex, or helper failures:**
  read [helpers-ingest](sub-skills/helpers-ingest/SKILL.md).
- **`Q`, `Search`, aggregations, mappings, `Document`, typed persistence, or
  high-level query composition:** read [dsl-search](sub-skills/dsl-search/SKILL.md).
- **ES|QL source/processing builders, safe parameters, or tabular results:** read
  [esql-query-builder](sub-skills/esql-query-builder/SKILL.md).
- **Shared install, serialization, version, or security failures:** read
  [troubleshooting.md](references/troubleshooting.md) in addition to the route.

For a cross-cutting task, load client-operations first, then the workflow route;
keep the client/auth configuration separate from request-body construction.

## Install and smoke check

The package supports Python 3.10+. Install only the extras used by the task:

```bash
python -m pip install elasticsearch
python -m pip install "elasticsearch[async]"       # aiohttp async transport
python -m pip install "elasticsearch[requests]"    # requests transport
python -m pip install "elasticsearch[orjson]"      # optional serializer
python -m pip install "elasticsearch[pyarrow]"     # Arrow/ES|QL workflows
python -m pip install "elasticsearch[vectorstore_mmr]"  # MMR helper support
```

```python
from elasticsearch import AsyncElasticsearch, Elasticsearch
print(Elasticsearch, AsyncElasticsearch)
```

An import proves package availability only. `client.info()` is a live service
probe and requires a reachable endpoint, credentials, and correct TLS.

## Guardrails

- Keep API keys, passwords, bearer tokens, CA files, and cluster URLs in runtime
  configuration or environment variables, not in generated guidance or logs.
- Prefer TLS verification with `ca_certs` or a supported fingerprint. Do not use
  `verify_certs=False` as a production solution.
- Generated client modules are specification output; do not edit files under
  `elasticsearch/_sync/client/` or `elasticsearch/_async/client/` to change an
  API. Upstream API changes belong in the Elasticsearch specification project.
- A bulk HTTP response can contain item failures. Inspect helper results and
  use bounded retries only for operations whose retry semantics are understood.
- A rendered DSL/ES|QL request is not server validation. Check target mappings,
  server version, privileges, response shape, and partial-result flags.
- Close clients: `client.close()` for sync and `await client.close()` for async,
  preferably with an async context manager.

## Verification entry points

Use the bundled offline checks when no cluster is available:

- `python sub-skills/helpers-ingest/scripts/bulk_actions_smoke.py`
- `python sub-skills/dsl-search/scripts/dsl_query_smoke.py`
- `python sub-skills/esql-query-builder/scripts/esql_query_smoke.py`

Read [routing metadata](references/repo-routing-metadata.json) only when the
managed repo-skill router is being rebuilt; it is structured metadata, not a
user workflow reference.
