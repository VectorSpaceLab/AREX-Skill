# Search Workflows

## Single-node search Flow

Start from the bundled [search-flow.yml](../scripts/search-flow.yml). Copy it into the user's project and edit `port`, `workspace`, `name`, and `n_dim` there.

```yaml
jtype: Flow
version: '1'
with:
  port: 61000
executors:
  - name: encoder
    uses:
      jtype: CLIPEncoder
      with:
        name: ViT-B-32::openai
      metas:
        py_modules:
          - clip_server.executors.clip_torch
  - name: indexer
    uses:
      jtype: AnnLiteIndexer
      with:
        n_dim: 512
        limit: 10
      metas:
        py_modules:
          - annlite.executor
    workspace: ./workspace
```

Install requirements:

```bash
pip install "clip-server[search]" clip-client
```

Start the server after approving model downloads and long-running service startup:

```bash
python -m clip_server search-flow.yml
```

## Index documents

```python
from clip_client import Client
from docarray import Document

client = Client("grpc://127.0.0.1:61000")
client.index([
    Document(id="text-1", text="she smiled, with pain"),
    Document(id="image-1", uri="/path/to/apple.png"),
    Document(id="image-2", uri="/path/to/bicycle.png"),
])
```

Use stable IDs when documents may later be updated or interpreted. Keep image files accessible to the process that creates the client request.

## Search by text

```python
result = client.search(["smile"], limit=2)
for match in result[0].matches:
    print(match.id, match.text, match.uri, match.scores)
```

The query is encoded by the same CLIP encoder, then AnnLite returns nearest neighbors. Text queries can retrieve image documents because CLIP embeds both modalities into a shared vector space.

## Search by image

```python
from docarray import Document

query = [Document(uri="/path/to/query-image.jpg")]
result = client.search(query, limit=5)
print(result[0].matches[:, ["id", "scores__cosine"]])
```

Use `Document` inputs when the query is an image. A raw string path may also be auto-detected by the client, but `Document(uri=...)` is clearer for agents.

## Sharded search Flow

For large corpora, shard the AnnLite executor and use polling rules that match indexing versus querying:

```yaml
executors:
  - name: encoder
    uses:
      jtype: CLIPEncoder
      metas:
        py_modules:
          - clip_server.executors.clip_torch
  - name: indexer
    uses:
      jtype: AnnLiteIndexer
      with:
        n_dim: 512
      metas:
        py_modules:
          - annlite.executor
    workspace: ./workspace
    shards: 5
    polling:
      /index: ANY
      /search: ALL
      /update: ALL
      /delete: ALL
      /status: ALL
```

`ANY` for `/index` prevents duplicate indexing. `ALL` for `/search` queries every shard so the global nearest neighbors are not hidden in an unqueried shard.

## Memory estimation

AnnLite memory has two major contributors:

- HNSW index: roughly `N * 1.1 * (4 bytes * dimension + 8 bytes * max_connection)`.
- Cell table: roughly linear in row count and stored columns; default no-filter columns are about 0.12 GB per million rows in the documented estimate.

Also budget for the running Jina Flow, CLIP model, preprocessing batches, and OS cache. Reduce memory pressure by lowering model dimension, limiting stored columns, sharding, reducing batch sizes, or choosing a smaller CLIP model.

## Dimension changes

Changing `name` from a 512-dimensional model to a 768/1024-dimensional model makes existing vectors incompatible. Update `n_dim` and rebuild the index; do not append new embeddings to an old workspace with the wrong dimension.
