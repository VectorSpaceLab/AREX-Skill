# Config and Data Formats

## `pixelrag.yaml`

Default config values verified from the package:

```python
DEFAULT_CONFIG = {
  "ingest": {"backend": "cdp", "quality": 85, "tile_height": 8192},
  "embed": {"model": "Qwen/Qwen3-VL-Embedding-2B", "device": "cuda"},
  "output": "./index",
}
```

Common keys:

```yaml
source:
  type: local      # local | web | pdf | kiwix
  path: ./docs     # local/pdf/kiwix depending on source type

ingest:
  backend: cdp
  quality: 85
  tile_height: 8192
  wait_network_idle: true   # defaulted for web source unless overridden

embed:
  model: Qwen/Qwen3-VL-Embedding-2B
  device: auto             # auto | cpu | mps | cuda
  gpu_ids: [0]             # GPU path
  backend: sglang          # GPU embedder option when selected

index:
  backend: faiss           # faiss | qdrant

output: ./index
```

## Source adapters

| Source type | Inputs | Notes |
| --- | --- | --- |
| `local` | Recursively finds `.pdf`, `.html`, `.htm`, `.png`, `.jpg`, `.jpeg`, `.md`, `.txt`. | Markdown/text are rendered to styled HTML before capture. |
| `pdf` | Recursively finds PDFs under `path`. | Each PDF page is treated as a natural chunk. |
| `web` | `urls_file` with one URL per line; optional preset such as `news`. | Web source defaults `wait_network_idle` to true. |
| `kiwix` | ZIM path served locally via Kiwix tooling. | Large Wikipedia-scale workflow; may launch Kiwix helper processes. |

## Tile and chunk manifests

- Web/local HTML tiles usually start as `tile_0000.jpg`, `tile_0001.jpg`, etc.
- The chunker writes `chunks.json` and 1024px-high chunk images.
- Wide tiles are split by width as well as height so chunks stay at or below the 875px embedding width.
- `article_id` is read from `chunks.json`, falls back to `tiles.json`, then to directory name or a stable SHA1-derived ID for legacy/non-numeric names.

## Embedding `.npz` files

CPU/local embedder writes arrays such as:

- `embeddings`: float vectors.
- `article_ids`: article IDs aligned to `articles.json`.
- `tile_indices`, `chunk_indices`, `y_offsets`, `tile_heights`: hit-location metadata used by serve.

GPU embedder output includes richer fields such as page heights, viewport widths, image hashes, and tile paths for large shard workflows.

## Index layouts

FAISS output includes:

```text
index/
  index.faiss
  metadata.npz
  summary.json
  articles.json
  tiles/
  embeddings/
```

Qdrant output stores vectors in the Qdrant collection and writes local summary/config metadata so `pixelrag serve` can infer the backend and collection.

## `articles.json`

Each entry contains a title, URL/path, and department. Serving uses the list index as the `article_id` lookup. Keep this file with the index directory.
