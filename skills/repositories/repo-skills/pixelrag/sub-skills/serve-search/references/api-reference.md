# Serve API Reference

## Start command

```bash
pixelrag serve \
  --index-dir ./index \
  --tiles-dir ./index/tiles \
  --articles-json ./index/articles.json \
  --port 30001
```

Key flags:

| Flag | Meaning |
| --- | --- |
| `--index-dir` | Directory with `summary.json`, FAISS files, metadata, or Qdrant summary. Env: `PIXELRAG_INDEX_DIR`. |
| `--tiles-dir` | Tile/chunk image directory. Env: `PIXELRAG_TILES_DIR`. |
| `--articles-json` | Article ID to title/URL/department mapping. Env: `PIXELRAG_ARTICLES_JSON`. |
| `--backend faiss|qdrant` | Override backend; otherwise inferred from `summary.json` or FAISS default. |
| `--qdrant-url`, `--qdrant-api-key`, `--qdrant-client-config`, `--collection` | Qdrant connection options. |
| `--model` | Query encoder model; default `Qwen/Qwen3-VL-Embedding-2B`. |
| `--device cpu|cuda` | Query encoder device. |
| `--peft-adapter` | Optional LoRA/PEFT adapter merged at load time. |
| `--render-on-demand`, `--kiwix-url`, `--zim-book` | Render retrieved Kiwix pages to tiles when no materialized tile corpus exists. |

## Endpoints

### `GET /health`

Returns `{"status":"ok"}` when the FastAPI app is up.

### `GET /status`

Returns index/model metadata:

- `total_vectors`
- `dimension`
- `nlist`
- `nprobe`
- `model`
- `index_dir`
- `tiles_dir`
- `index_built_at`
- `index_size_bytes`
- `metadata_size_bytes`

### `POST /search`

Request fields:

```json
{
  "queries": [{"text": "question"}],
  "n_docs": 10,
  "nprobe": 128,
  "min_tile_height": 200,
  "instruction": "Retrieve images or text relevant to the user's query.",
  "include_images": false,
  "articles_only": false,
  "department": "hr"
}
```

Each query can contain exactly one mode:

- `text`: text query encoded by the server.
- `image`: base64-encoded query image.
- `embedding`: precomputed vector.

Do not mix precomputed embeddings with text/image queries in the same request.

Response shape:

```json
{
  "results": [{
    "hits": [{
      "score": 0.73,
      "vector_id": 123,
      "article_id": 4,
      "tile_index": 0,
      "chunk_index": 2,
      "y_offset": 2048,
      "tile_height": 1024,
      "path": "4.png.tiles/chunk_0000_02.png",
      "url": "...",
      "article_pages": "0:0-4",
      "image_base64": null
    }]
  }]
}
```

### `GET /departments`

Lists departments and document counts when `articles.json` includes department metadata.

### `POST /reconstruct`

Debug endpoint:

```json
{"vector_ids": [1, 5, "qdrant-id"]}
```

Returns stored embeddings for alignment checks.

### `GET /tile/{article_id}/{tile_index}/{chunk_index}`

Serves the tile/chunk image by logical coordinates. Prefer this over legacy path-based tile reads.

## Query logging

If query logging is enabled, logs include request ID, source header, query text, image presence, `n_docs`, and department. Avoid logging sensitive user queries unless policy permits it.
