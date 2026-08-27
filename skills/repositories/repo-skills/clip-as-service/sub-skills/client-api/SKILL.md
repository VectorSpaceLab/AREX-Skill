---
name: client-api
description: "Guides clip_client.Client connectivity, encoding, ranking,
  indexing, searching, async calls, callbacks, and client-side troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Client API

Use this sub-skill when the user wants to call CLIP-as-service from Python or diagnose client-side behavior against an already-running server.

## Trigger examples

- "Use `clip_client.Client` to encode these text and image inputs."
- "Why does `Client.profile()` fail with `AioRpcError`?"
- "Rank text prompts against an image using CLIP-as-service."
- "Use async `aencode` or callbacks for a large stream."
- "Call `index`/`search` from the client after my search Flow is running."

## Read first

- [references/api-reference.md](references/api-reference.md) for verified method signatures, parameters, return types, input rules, and endpoint mapping.
- [references/workflows.md](references/workflows.md) for copyable recipes: connectivity profile, encoding, DocArray inputs, ranking, async calls, and client calls for search.
- [references/troubleshooting.md](references/troubleshooting.md) for invalid scheme, direct string input, empty input, missing embeddings, connectivity, TLS/auth, non-unique IDs, and callback issues.
- [scripts/check_client_api.py](scripts/check_client_api.py) to verify client imports/signatures safely; it only contacts a server when `--server` is supplied.

## Boundary routing

- If the server is not started yet or the user needs Flow YAML, model/runtime choice, Docker, TLS certificates, replicas, or monitoring, route to [server-runtime](../server-runtime/SKILL.md).
- If the task is to build the AnnLite search Flow, validate `n_dim`, or reason about sharding/polling, route to [search-retrieval](../search-retrieval/SKILL.md).
- If the task is only package installation or optional dependency diagnosis, also read the root [install map](../../references/install-and-package-map.md).

## Minimal client pattern

```python
from clip_client import Client

client = Client("grpc://0.0.0.0:51000")
latency = client.profile()
embeddings = client.encode(["a red car", "a blue bicycle"])
print(latency, embeddings.shape)
```

Use TLS schemes (`grpcs`, `https`, `websockets`/`wss`) only when the server was started with matching TLS configuration. Use `credential={"Authorization": "<token>"}` or the `CLIP_AUTH_TOKEN` environment variable for authenticated gRPC/HTTP endpoints.

## Input and output rules to preserve

- Passing a single bare string to `encode`, `index`, or `search` is an error; wrap it in a list.
- `encode(list[str])` returns a NumPy array. `encode(DocumentArray)` or `encode(list[Document])` returns a `DocumentArray` containing the same objects with embeddings filled.
- Ranking expects each root `Document` to have cross-modal candidates in `.matches` unless `source` is overridden.
- Empty inputs return empty list/`DocumentArray` depending on input type and method.
- Order and complete result gathering rely on unique `Document.id` values.

## Common decision points

1. **Protocol:** match the URI scheme to the server (`grpc`, `http`, or `websocket`; add `s` for TLS variants).
2. **Input representation:** use strings for simple text/image URIs; use `Document`/`DocumentArray` when you need explicit text/uri/blob/tensor fields, nested matches, chunks, or metadata preservation.
3. **Batching:** adjust `batch_size` and `prefetch` for memory/network behavior; very large streams may warn when length is unknown or high.
4. **Callbacks:** if `on_done`/`on_always` owns result collection, methods can return `None` instead of assembled results.
5. **Search client calls:** `Client.index` and `Client.search` require a server Flow with an indexer. An encoder-only server can encode/rank but not search a corpus.

## Verification hints

Run the safe signature check before writing code in an unfamiliar environment:

```bash
python sub-skills/client-api/scripts/check_client_api.py
```

If a real server is available and the user approves a network call, profile it explicitly:

```bash
python sub-skills/client-api/scripts/check_client_api.py --server grpc://127.0.0.1:51000 --profile
```
