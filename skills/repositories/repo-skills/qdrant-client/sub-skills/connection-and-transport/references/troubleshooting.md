# Connection and Transport Troubleshooting

## Server Version Compatibility Warning

Symptom: construction emits a warning like `Failed to obtain server version` or `client version ... is incompatible with server version ...`.

Cause: by default, remote construction starts a background compatibility check against the REST endpoint. The warning can mean the server is not reachable, credentials are missing, TLS/proxy settings are wrong, or the server version is outside the supported client/server compatibility window.

Fix:

- For real connections, verify URL, API key, TLS, proxy, and server health.
- For offline config tests, examples, or unit tests that only validate constructor behavior, pass `check_compatibility=False`.
- Do not treat `check_compatibility=False` as a connectivity check; it skips one.

## Insecure API Key Warning

Symptom: `Api key is used with an insecure connection.`

Cause: `api_key` was supplied while the resolved scheme is HTTP. Qdrant Cloud and production API-key deployments should use HTTPS.

Fix:

```python
client = QdrantClient(url="https://qdrant.example.com:6333", api_key="<key>")
```

If you are intentionally testing against a local HTTP server, keep the warning in mind and avoid using production credentials.

## Auth Token Provider over HTTP

Symptom: `Auth token provider is used with an insecure connection.`

Cause: `auth_token_provider` sends bearer tokens over the resolved HTTP transport.

Fix: use an HTTPS URL for bearer-token deployments. Keep HTTP only for isolated local tests with non-sensitive tokens.

## Duplicate API-Key Header

Symptom: warning that `api-key` passed in `headers` will be overridden by the `api_key` parameter.

Cause: the constructor accepts both generic headers and the dedicated `api_key` argument. The dedicated argument intentionally wins and is propagated to REST headers and gRPC metadata.

Fix: remove `api-key` from `headers`; pass only `api_key="..."` and reserve `headers` for non-auth metadata such as request IDs or tenant hints.

## Prefix Conflicts

Symptom: `ValueError: Prefix can be set either in url or in prefix`.

Cause: both `url` contains a path and `prefix` was passed separately.

Fix: use exactly one prefix source:

```python
QdrantClient(url="https://proxy.example.com/qdrant", check_compatibility=False)
# or
QdrantClient(url="https://proxy.example.com", prefix="qdrant", check_compatibility=False)
```

## Host Contains Protocol

Symptom: `ValueError` explaining that `host` is not expected to contain protocol.

Cause: `host="https://qdrant.example.com"` was used.

Fix: either use `url="https://qdrant.example.com:6333"` or strip the scheme and pass `host="qdrant.example.com", https=True`.

## Only One Location Selector

Symptom: `Only one of <location>, <url>, <host> or <path> should be specified.`

Cause: local and remote selectors were mixed, such as `QdrantClient(":memory:", url="...")` or `QdrantClient(url="...", path="...")`.

Fix: choose local mode (`":memory:"` or `path=`) or remote mode (`url` or `host`) for a single client. Use separate clients for separate backends.

## gRPC Compression Deflate Unsupported

Symptom: constructing with `grpc_compression=Compression.Deflate` raises `ValueError`; passing a string like `"gzip"` raises `TypeError`.

Cause: qdrant-client accepts `grpc.Compression` enum values and explicitly rejects Deflate.

Fix:

```python
from grpc import Compression

QdrantClient(prefer_grpc=True, grpc_compression=Compression.Gzip)
QdrantClient(prefer_grpc=True, grpc_compression=Compression.NoCompression)
```

## Pool Size and Limits Conflict

Symptom: `ValueError` says `pool_size` and `limits` are mutually exclusive.

Cause: `pool_size` is a high-level connection-pool control, while `limits` is a direct HTTPX limits object. qdrant-client will not combine them.

Fix: choose one:

```python
QdrantClient(url="https://qdrant.example.com:6333", pool_size=8)
# or
import httpx
QdrantClient(url="https://qdrant.example.com:6333", limits=httpx.Limits(max_connections=8))
```

## Closed Client

Symptom: after `client.close()`, REST calls fail with response-handling errors, gRPC initialization can raise `RuntimeError: Client was closed. Please create a new QdrantClient instance.`, and local mode raises `RuntimeError` for operations.

Cause: close is final for that client object.

Fix: structure code so each client is closed only at the end of its scope, and create a new `QdrantClient` for later work.

## Async Token Provider on Sync Client

Symptom: sync `QdrantClient` with an async `auth_token_provider` fails during a sync REST call with `Synchronous token provider is not set` or during sync gRPC metadata creation with `Synchronous channel requires synchronous auth token provider.`

Cause: the sync client cannot await token providers during sync operations.

Fix: use a synchronous function with `QdrantClient`, or move the workflow to `AsyncQdrantClient` and the `async-client` sub-skill.

## Custom User-Agent Is Overridden

Symptom: warning that `User-Agent` or `grpc.primary_user_agent` will be overridden.

Cause: qdrant-client manages its own user-agent containing the qdrant-client and Python versions.

Fix: avoid relying on custom user-agent values for routing. Use separate headers such as `x-request-id` or `x-tenant` for application metadata.

## SSL Option Names

Symptom: warning that an SSL option should be used without the `grpc.` prefix, or `TypeError` for SSL credential values.

Cause: custom gRPC SSL credential options are parsed as `root_certificates`, `private_key`, and `certificate_chain`, and values must be bytes.

Fix: pass byte strings under the unprefixed names inside `grpc_options`.
