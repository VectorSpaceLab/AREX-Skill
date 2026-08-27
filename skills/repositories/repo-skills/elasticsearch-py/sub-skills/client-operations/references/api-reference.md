# Client API reference

The installed package at the source snapshot exposes `elasticsearch.__version__`
`(9, 5, 0)` and requires `elastic-transport>=9.4.1,<10`. The client supports
Python 3.10 and later.

## Constructors

`Elasticsearch(hosts=None, *, cloud_id=None, api_key=None, basic_auth=None,
bearer_auth=None, headers=DEFAULT, http_compress=DEFAULT,
verify_certs=DEFAULT, ca_certs=DEFAULT, client_cert=DEFAULT, client_key=DEFAULT,
ssl_assert_hostname=DEFAULT, ssl_assert_fingerprint=DEFAULT, ssl_context=DEFAULT,
request_timeout=DEFAULT, transport_class=Transport, node_class=DEFAULT,
node_pool_class=DEFAULT, node_selector_class=DEFAULT, max_retries=DEFAULT,
retry_on_status=DEFAULT, retry_on_timeout=DEFAULT, sniff_on_start=DEFAULT,
sniff_before_requests=DEFAULT, sniff_on_node_failure=DEFAULT, sniff_timeout=DEFAULT,
serializer=None, serializers=DEFAULT, default_mimetype="application/json", ...)`.

`AsyncElasticsearch` has the same connection/configuration concepts but uses
`AsyncTransport`; its default HTTP implementation needs the `aiohttp` extra.
The full signature includes `http_compress`, TLS settings, timeouts, retries,
sniffing, serializers, node pools, and `transport_class`.

Use one of these common forms:

```python
Elasticsearch("https://host:9200", api_key=os.environ["ELASTIC_API_KEY"])
Elasticsearch(cloud_id=os.environ["ELASTIC_CLOUD_ID"],
              basic_auth=(os.environ["ES_USER"], os.environ["ES_PASSWORD"]))
Elasticsearch(["https://node-a:9200", "https://node-b:9200"],
              ca_certs="http_ca.crt", basic_auth=(user, password))
```

## Request and options

Generated methods accept API-specific keyword arguments, for example:
`client.indices.create(index="books", mappings={...})`,
`client.index(index="books", id="1", document={...})`,
`client.get(index="books", id="1")`,
`client.search(index="books", query={"match": {"title": "python"}})`, and
`client.update(index="books", id="1", doc={...})`.

Use `client.options(...)` to create a configured copy for a request or a group
of requests:

```python
client.options(ignore_status=404).indices.delete(index="temporary")
authenticated = client.options(api_key=os.environ["ELASTIC_API_KEY"])
```

The returned response is a typed response wrapper with dictionary-like access;
inspect the documented response fields rather than assuming every response is a
plain `dict`.

## Errors and versions

Catch the narrowest applicable exception from `elasticsearch.exceptions`, such
as `NotFoundError`, `ConflictError`, `BadRequestError`,
`AuthenticationException`, `AuthorizationException`, `ConnectionError`,
`ConnectionTimeout`, `SSLError`, or `UnsupportedProductError`. Keep the error
body and HTTP status in diagnostics, but redact credentials and tokens.

Client versions are forward compatible across equivalent and later minor
server versions, but new server features require a matching client. Upgrade the
server before moving to a new major client, and check the package's compatibility
policy before using a newly added API.
