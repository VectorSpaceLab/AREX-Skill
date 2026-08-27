# Cross-cutting troubleshooting

Use the nearest sub-skill troubleshooting reference for workflow-specific
failures; this page covers package-wide diagnosis.

## Installation and imports

The distribution is `elasticsearch`, imports as `elasticsearch`, and requires
Python 3.10+ plus `elastic-transport>=9.4.1,<10`. Install only the selected
extras (`async`, `requests`, `orjson`, `pyarrow`, or `vectorstore_mmr`). Run
`python -m pip check` and a small import check before diagnosing a cluster.

## Service and security

Separate these checks in order: package import, client constructor/configuration,
and a bounded live `client.info()` call. For TLS failures, verify the endpoint,
CA certificate, hostname, or fingerprint; retain certificate verification. For
auth failures, verify credential type and privileges without logging secrets.
Cloud ID is preferred for Elastic Cloud; self-managed HTTPS generally needs the
cluster CA or a supported fingerprint.

## API and version behavior

Generated API namespaces and method parameters are versioned. A rejected
keyword or unsupported endpoint can indicate a client/server mismatch or an
incorrect parameter name; inspect the current signature and compatibility policy
rather than constructing raw URLs by guesswork. Catch a specific
`elasticsearch.exceptions` class when possible and preserve status/body metadata
with sensitive fields redacted.

## Requests, serialization, and lifecycle

A request timeout, transport retry, and server API timeout are different
controls. Set them deliberately and consider write idempotency. If JSON
serialization fails, normalize values or select an appropriate serializer; do
not silently stringify structured data. Async clients need `aiohttp` and must be
closed with `await client.close()` or an async context manager.

For bulk, DSL, and ES|QL-specific failures, follow the routes from the root
router and read their linked references. Offline bundled smoke scripts validate
request/action construction but cannot prove service connectivity, server
privileges, mappings, or ES|QL feature support.
