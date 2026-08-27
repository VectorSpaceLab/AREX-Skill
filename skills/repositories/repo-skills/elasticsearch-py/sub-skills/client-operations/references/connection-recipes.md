# Connection recipes

## Elastic Cloud

Prefer the Cloud ID form because it configures HTTPS and compression for the
cloud deployment. Keep secrets outside code:

```python
client = Elasticsearch(
    cloud_id=os.environ["ELASTIC_CLOUD_ID"],
    api_key=os.environ["ELASTIC_API_KEY"],
)
print(client.info())
```

Basic authentication is also supported with `basic_auth=(user, password)`.
For asynchronous code, use `AsyncElasticsearch` and `await client.info()`.

## Self-managed HTTPS

Use the generated CA certificate when available:

```python
client = Elasticsearch(
    "https://localhost:9200",
    ca_certs="http_ca.crt",
    basic_auth=("elastic", os.environ["ELASTIC_PASSWORD"]),
)
```

On Python 3.10+, a synchronous client can instead verify the server with
`ssl_assert_fingerprint="SHA256 fingerprint"`. The fingerprint method is not
available with the `aiohttp` HTTP client used by `AsyncElasticsearch`; use the
CA certificate for async clients. Colons and case in the fingerprint are
accepted. `openssl x509 -fingerprint -sha256 -noout -in http_ca.crt` calculates
a fingerprint for a local CA file.

## Authentication choices

- `api_key`: API key string or `(id, key)` tuple.
- `basic_auth`: username/password tuple.
- `bearer_auth`: service-account or bearer token string.
- `.options(...)`: per-request or derived-client override.

Never put passwords, API keys, bearer tokens, or private CA material in a
committed skill, test fixture, or log.

## Multiple nodes and transport policy

Pass a list of URLs or node configurations when the client should distribute
requests across nodes. Configure `node_selector_class` when round-robin is not
the desired selection policy. Use `connections_per_node`, `max_retries`,
`retry_on_status`, `retry_on_timeout`, `retry_backoff_base`, and
`retry_backoff_cap` only after deciding which operations are safe to retry.
Sniffing (`sniff_on_start`, `sniff_before_requests`, or
`sniff_on_node_failure`) can be inappropriate behind load balancers or when
sniffed private addresses are unreachable.

## Async lifecycle

```python
async with AsyncElasticsearch(
    os.environ["ES_URL"],
    api_key=os.environ["ELASTIC_API_KEY"],
) as client:
    response = await client.search(index="books", query={"match_all": {}})
```

If an async context manager is not used, call `await client.close()` in a
`finally` block. An `Unclosed client session` warning means the async client or
its transport was not closed; it is not harmless cleanup noise in long-running
services.
