# Index-Build Workflows

## End-to-end local index

Create a `pixelrag.yaml`:

```yaml
source:
  type: local
  path: ./my_docs

ingest:
  backend: cdp
  quality: 85
  tile_height: 8192

embed:
  model: Qwen/Qwen3-VL-Embedding-2B
  device: auto

output: ./my_index
```

Then run:

```bash
pixelrag index build --config pixelrag.yaml --limit 10
```

Use `--limit` for smoke runs. Use `--force` only when you intentionally want to delete old `tiles/` and `embeddings/` and rebuild them.

## Stage-by-stage path

Use this when you already rendered tiles or need to debug one stage:

```bash
pixelrag chunk --tiles-dir ./tiles --workers 8
pixelrag embed --shard-dir ./tiles --output-dir ./embeddings --gpu-ids 0
pixelrag build-index build --embeddings-dir ./embeddings --output-dir ./index
```

For small local CPU/MPS runs, the local embedder module is exposed by the stage implementation:

```bash
python -m pixelrag_embed.embed_cpu --shard-dir ./tiles --output-dir ./embeddings --device auto --limit 5
```

## Qdrant backend

Qdrant is useful for shared collections, payload filtering, quantization, or disk-backed vector storage.

```yaml
index:
  backend: qdrant
  qdrant_url: http://localhost:6333
  collection: pixelrag
  client_config: ./qdrant-client.json
  quantization_config: ./quantization.json
  append: false
  recreate: false
```

Build with:

```bash
pixelrag build-index build --embeddings-dir ./embeddings --output-dir ./index \
  --backend qdrant --qdrant-url http://localhost:6333 --collection pixelrag
```

Use exactly one of:

- no flag: fail if collection state is incompatible.
- `--append`: upsert into an existing collection.
- `--recreate`: delete and recreate the collection.

## Incremental reruns

The orchestrator assigns sequential article IDs from the current source order. To avoid stale pixels after files are added/removed/reordered, it stamps `source` and `article_id` into manifests and re-renders a tile directory when the recorded source does not match the current document at that position.

Guidance:

- Let the orchestrator manage `tiles/` under the output directory.
- Do not manually rename tile directories between runs.
- Use `--force` when a clean rebuild is clearer than incremental repair.
- If a corrupt manifest appears, the affected tile directory should be re-rendered rather than relabeled.

## Department-filtered local indexes

For `source.type: local`, the first subdirectory under the source root becomes the `department` field in `articles.json`. Files directly under the source root have an empty department.

Example:

```text
my_docs/
  hr/policy.pdf          -> department "hr"
  finance/report.md      -> department "finance"
  readme.txt             -> department ""
```

`serve-search` can later pre-filter by department using `/departments` and the `department` field in `/search`.
