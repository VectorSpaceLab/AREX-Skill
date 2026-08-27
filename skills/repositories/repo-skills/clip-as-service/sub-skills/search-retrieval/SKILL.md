---
name: search-retrieval
description: "Guides CLIP-as-service search flows with CLIPEncoder plus AnnLite
  indexing, querying, dimensions, sharding, and retrieval troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Search and Retrieval

Use this sub-skill when the user wants CLIP-as-service to index a corpus and search across text/image embeddings, usually with a Jina Flow containing `CLIPEncoder` followed by `AnnLiteIndexer`.

## Trigger examples

- "Build text-to-image search with CLIP-as-service."
- "Write `search_flow.yml` for CLIPEncoder + AnnLiteIndexer."
- "What should `n_dim` be for `ViT-L-14`?"
- "Why does `/search` return incomplete results in a sharded Flow?"
- "Use `Client.index` and `Client.search` after starting a search server."

## Read first

- [references/workflows.md](references/workflows.md) for single-node and sharded CLIP Search setup, indexing, querying, and cross-modal examples.
- [references/configuration.md](references/configuration.md) for Flow YAML fields, AnnLite parameters, `n_dim`, workspace, sharding, and polling.
- [references/troubleshooting.md](references/troubleshooting.md) for missing AnnLite, endpoint, dimension, workspace, empty result, and sharding failures.
- [scripts/search-flow.yml](scripts/search-flow.yml) for a self-contained starter template.
- [scripts/check_search_config.py](scripts/check_search_config.py) for static validation without starting a model or indexer.

## Boundary routing

- Use [server-runtime](../server-runtime/SKILL.md) to select CLIP model/runtime, install optional backends, tune replicas/protocol/TLS/monitoring, or start the encoder service.
- Use [client-api](../client-api/SKILL.md) for detailed `clip_client.Client` input/output behavior, callbacks, async methods, authentication, and connectivity errors.
- Use this sub-skill only for retrieval/index-specific configuration and operation.

## Minimal search architecture

A search Flow has two stages:

1. `CLIPEncoder` converts incoming text/image documents into embeddings.
2. `AnnLiteIndexer` stores and retrieves vectors with a dimension matching the selected CLIP model.

The client does not call `encode()` explicitly before indexing; `Client.index()` sends documents through the Flow and the encoder fills embeddings before the indexer stores them.

## Minimal client use after server startup

```python
from clip_client import Client
from docarray import Document

client = Client("grpc://127.0.0.1:61000")
client.index([
    Document(id="caption-1", text="a photo of a red car"),
    Document(id="caption-2", text="a photo of a blue bicycle"),
])

results = client.search(["red vehicle"], limit=2)
for match in results[0].matches:
    print(match.id, match.scores)
```

## Critical decisions

- Set AnnLite `n_dim` to the chosen CLIP model output dimension. Default `ViT-B-32::openai` uses 512.
- Keep a stable `workspace` for persistent indexes. Changing model dimension or incompatible indexer configuration requires rebuilding.
- For sharded indexes, use `ANY` polling for `/index` so each document is indexed once; use `ALL` for `/search` so queries reach all shards.
- Search flows need the `clip-server[search]` extra or an environment with AnnLite installed.

## Safe validation sequence

```bash
python sub-skills/search-retrieval/scripts/check_search_config.py sub-skills/search-retrieval/scripts/search-flow.yml --model-name ViT-B-32::openai
```

Then start a service only after the user approves model downloads and long-running server processes.
