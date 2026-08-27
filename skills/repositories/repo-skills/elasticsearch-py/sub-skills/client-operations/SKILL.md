---
name: client-operations
description: "Guide Elasticsearch Python client installation, synchronous and
  asynchronous connections, authentication, TLS, transport configuration, API
  calls, and client lifecycle troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Client operations

Use this route when the task is about the official `elasticsearch` Python
client: installation, `Elasticsearch` or `AsyncElasticsearch`, connecting to a
cluster, authentication, TLS, generated API calls, transport behavior, or
async resource cleanup.

## Fast route

1. Install the base distribution (`python -m pip install elasticsearch`) on
   Python 3.10+. Add `[async]` for the `aiohttp` async transport, `[requests]`
   for the requests transport, `[orjson]` for the optional serializer, and
   `[pyarrow]` or `[vectorstore_mmr]` only for workflows that use them.
2. Choose the client from the execution model. Use `Elasticsearch` for normal
   synchronous code and `AsyncElasticsearch` inside an async event loop. Do not
   mix an async client with synchronous helper functions.
3. Choose a connection form: `cloud_id` for Elastic Cloud, an HTTPS URL plus
   `basic_auth`, `api_key`, or `bearer_auth` for a managed/self-managed service,
   and `ca_certs` or `ssl_assert_fingerprint` for TLS verification.
4. Validate with `client.info()` only when a reachable cluster and credentials
   exist. Package-only checks can instantiate a client and inspect transport
   configuration without making a request.
5. Route bulk/scan/reindex to [helpers-ingest](../helpers-ingest/SKILL.md),
   high-level `Search`/`Q`/`Document` work to [dsl-search](../dsl-search/SKILL.md),
   and ES|QL construction to [esql-query-builder](../esql-query-builder/SKILL.md).

Read [api-reference.md](references/api-reference.md) for verified constructor,
request, and option details; use [connection-recipes.md](references/connection-recipes.md)
for connection patterns; and read [troubleshooting.md](references/troubleshooting.md)
before changing TLS, retries, optional dependencies, or server compatibility.

## Minimal import check

```python
from elasticsearch import AsyncElasticsearch, Elasticsearch

client = Elasticsearch("http://localhost:9200", request_timeout=5)
print(type(client).__name__)
client.close()
```

The snippet does not prove that a cluster is reachable. Keep credentials in
environment variables or a secret manager, never in source or prompts. For
async code, close with `await client.close()` in a `finally` block or use the
client's async context-management support.

## Operating rules

- Use the client-generated API namespaces (`client.indices`, `client.cluster`,
  `client.security`, etc.) and keyword arguments matching the current client
  version; do not edit generated files under the package's client directories.
- Prefer explicit TLS verification. `verify_certs=False` is a diagnostic-only
  exception, not a production fix.
- Set request timeouts and retry behavior based on the operation. Transport
  retries are not a substitute for idempotency or application-level error
  handling; inspect `ApiError` subclasses and response metadata.
- Use `.options(...)` for per-request overrides such as auth, `ignore_status`,
  headers, or request options while retaining the base client configuration.
- Treat a successful import, a successful constructor, and a successful
  `client.info()` as three different checks: package, configuration, and live
  service respectively.
