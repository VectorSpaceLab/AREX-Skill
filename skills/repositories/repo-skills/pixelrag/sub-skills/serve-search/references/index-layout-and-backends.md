# Index Layout and Backends

## Required local files

For FAISS serving, keep these together:

```text
index/
  index.faiss
  metadata.npz
  summary.json
  articles.json
  tiles/
```

`metadata.npz` maps vector rows to `article_id`, `tile_index`, `chunk_index`, `y_offset`, and `tile_height`. `articles.json` maps article IDs to titles/URLs/departments.

## FAISS backend

FAISS loads `index.faiss` and `metadata.npz`. Set:

```bash
PIXELRAG_INDEX_MMAP=1 pixelrag serve --index-dir ./large_index --port 30001
```

when startup time and RAM pressure matter for very large indexes. Memory mapping pages inverted lists on demand and relies on the OS page cache.

Department filtering uses FAISS ID selectors over vector positions for the selected article IDs, so filtered search should still return `k` hits when enough department vectors exist.

## Qdrant backend

Qdrant mode requires a reachable Qdrant server or local path configured through `--qdrant-url` or `--qdrant-client-config`.

```bash
pixelrag serve --index-dir ./index \
  --backend qdrant \
  --qdrant-url http://localhost:6333 \
  --collection pixelrag
```

Payload fields must include:

- `article_id`
- `tile_index`
- `chunk_index`
- `y_offset`
- `tile_height`

`min_tile_height` and `article_ids` filters are pushed into Qdrant payload filters.

## Tiles and image returns

When `include_images` is false, hits include coordinates and a relative path. Clients can fetch images with `/tile/{article_id}/{tile_index}/{chunk_index}`.

When `include_images` is true:

- If a materialized tile exists, the API returns base64 bytes.
- If `--render-on-demand` is enabled, PixelRAG renders from Kiwix in a worker thread and returns base64 for that chunk.
- Payloads can be large; lower `n_docs` for chat-agent calls.

## On-demand Kiwix rendering

Use this only when the index references Kiwix/Wikipedia pages and full tiles are not materialized. It needs a running Kiwix HTTP service and a correct book ID. First queries may be slow; raise client timeouts for benchmark harnesses.

## Query encoder and adapters

Text and image query modes load `Qwen/Qwen3-VL-Embedding-2B` by default. CUDA can reduce latency but requires compatible torch/CUDA wheels and enough memory. `--peft-adapter` can load a LoRA adapter on top of the base encoder for indexes built with that adapter.

Embedding-mode queries bypass the encoder and are useful for alignment/debugging, but all queries in one request must be embedding-mode if any are.
