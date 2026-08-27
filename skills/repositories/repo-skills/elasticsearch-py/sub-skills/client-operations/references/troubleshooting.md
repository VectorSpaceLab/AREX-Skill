# Client troubleshooting

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ImportError` mentioning `elastic-transport` | Incompatible transport version | Install a version satisfying `elastic-transport>=9.4.1,<10`; do not edit generated client files. |
| `ImportError` for async transport | `aiohttp` is not installed | Install `elasticsearch[async]`; use the synchronous client if the application is not async. |
| TLS certificate verify failure | Missing CA, wrong certificate, hostname mismatch, or stale fingerprint | Confirm the HTTPS endpoint, use the cluster's CA with `ca_certs`, or recalculate `ssl_assert_fingerprint`; do not disable verification as the final fix. |
| `AuthenticationException`/`AuthorizationException` | Wrong credential or insufficient privilege | Verify the secret source and required Elasticsearch privileges; redact credentials from logs. |
| `ConnectionError` or `ConnectionTimeout` | Service is down, URL is wrong, DNS/firewall issue, or timeout too short | First run a bounded `client.info()` probe, verify the service independently, then adjust `request_timeout` and retry policy. |
| Requests reach an unusable private node | Sniffing behind a load balancer or NAT | Disable sniffing or provide a `sniffed_node_callback` that produces reachable node configs. |
| Unexpected 404/409 | Missing index/document or conflicting create/update | Inspect the exception status/body; use `ignore_status` only when the absence is an expected branch. |
| A new API keyword is rejected | Client/server version mismatch or wrong generated API parameter | Check the client/server compatibility policy and current method signature; do not pass arbitrary URL names as keywords. |
| `UnsupportedProductError` | Endpoint is not an Elasticsearch product or proxy altered the response | Verify the endpoint and proxy behavior before changing product checks. |
| `Unclosed client session` | `AsyncElasticsearch` was not closed | Use `async with` or `await client.close()` in `finally`. |
| JSON serialization error | Unsupported Python value or optional serializer mismatch | Normalize the document to JSON-compatible values, use `JsonSerializer`, or install/configure `orjson` only when needed. |

When diagnosing a live request, capture method, URL host (not credentials),
status, request id, and redacted response metadata. Avoid retrying non-idempotent
writes blindly; use application-level idempotency and inspect partial results.
