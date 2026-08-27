# Client Troubleshooting

## Connection and protocol failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ValueError: <server> is not a valid scheme` | URI scheme is not one of `grpc`, `http`, `websocket`, `grpcs`, `https`, `websockets`, or `wss`. | Rewrite the endpoint as `scheme://host:port`; match the scheme to the server Flow protocol. |
| `AioRpcError`, `StatusCode.UNAVAILABLE`, `failed to connect to all addresses` | Server is not running, wrong host/port, firewall/security group, protocol mismatch, or TLS mismatch. | Run `client.profile()` against the exact URI; verify server console endpoint, protocol, TLS suffix, port exposure, and network reachability. |
| HTTP call works but gRPC fails, or the reverse | Client scheme does not match Flow protocol. | Use the protocol configured under the Flow's top-level `with.protocol`; default examples commonly use gRPC. |
| Authenticated endpoint rejects requests | Missing or wrong `Authorization` header/metadata. | Pass `credential={"Authorization": token}` or set `CLIP_AUTH_TOKEN`; for websocket, this client warns because credentials are not supported. |

## Input and result errors

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Content must be an Iterable... try .encode(["..."])` | A bare string was passed to `encode`, `index`, or `search`. | Wrap a single text or URI in a list. |
| `.rank()` says every doc must have `.matches` | Ranking roots have no candidate matches. | Build `Document(..., matches=[...])` or pass `source=<field>` if candidates are stored elsewhere. |
| Empty input returns different types | Method preserves the input family. | For `encode([])`, expect `[]`; for `encode(DocumentArray())`, expect empty `DocumentArray`; rank/index/search return empty `DocumentArray`. |
| Returned results are incomplete or out of order | Duplicate user-supplied `Document.id` values collide during gather. | Ensure every `Document.id` is unique or let DocArray auto-generate IDs. |
| `Empty embedding returned from the server` | Server Flow is misconfigured, wrong port is used, or the server failed internally. | Restart the server, profile the endpoint, confirm it contains a CLIP encoder, and retry with a tiny batch. |
| Very large request warns about invalid inputs or progress accuracy | Unknown generator length or total length above the progress threshold. | Validate inputs before streaming; use explicit lists for bounded jobs or callbacks for external sinks. |

## Image handling pitfalls

- For a `Document` with both `.text` and `.uri`, the client treats it as text first. Split mixed content into separate documents when both modalities should be embedded.
- `.tensor` image inputs should be height-width-channel arrays. Server preprocessing converts tensors to blobs internally.
- Remote image URLs can fail for network reasons before the server sees the request. For reliable batch jobs, prefer accessible local files or already-validated object storage URLs.
- Loading many images into `.blob` can exhaust client memory. Prefer `.uri` unless the user explicitly needs to send bytes.

## Callback pitfalls

If `on_done` or `on_always` is supplied, the client may not build an internal `DocumentArray`; the return value can be `None`. Use callbacks when streaming into another sink. If the caller needs an assembled return, omit callbacks or make the callback append results to an explicit collection.

## Search-specific client failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `/index` or `/search` endpoint fails but `/encode` works | Server Flow has no indexer executor. | Build a CLIP Search Flow in [search-retrieval](../../search-retrieval/SKILL.md). |
| `search(..., limit=k)` returns fewer matches than expected | Not enough documents indexed, shards misconfigured, or query reached only part of the index. | Check index count/workspace; for sharded AnnLite, use `/search: ALL` polling. |
| Search score dimensions or index build fails | `n_dim` does not match the selected CLIP model output dimension. | Validate the Flow with the search-retrieval `check_search_config.py` helper and rebuild incompatible indexes. |

## Safe diagnostic helper

```bash
python sub-skills/client-api/scripts/check_client_api.py
python sub-skills/client-api/scripts/check_client_api.py --server grpc://127.0.0.1:51000 --profile
```

The first command is import/signature-only. The second contacts a user-supplied server.
