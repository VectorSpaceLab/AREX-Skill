---
name: index-build
description: "Use PixelRAG to build visual retrieval indexes from rendered
  documents, tile chunks, embeddings, FAISS, or Qdrant."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# PixelRAG Index Build

Use this sub-skill when a task asks to make documents searchable with PixelRAG, build a local visual index, debug `pixelrag.yaml`, run chunk/embed/build-index stages, or choose FAISS versus Qdrant.

## Start Here

1. If the user only has URLs, PDFs, HTML, or images and no tiles yet, first read `../render-capture/SKILL.md`.
2. Pick an orchestration level:
   - End-to-end: `pixelrag index build --config pixelrag.yaml`.
   - Stage-by-stage: `pixelrag chunk`, `pixelrag embed`, and `pixelrag build-index`.
3. Decide device and backend:
   - `device: auto` chooses CUDA, MPS, then CPU in the local embedder path.
   - CPU/MPS is suitable for small demos; full Qwen embedding on CPU is slow.
   - FAISS is the default local backend; Qdrant is for server-backed or disk/quantized vector storage.
4. Validate generated artifacts before serving: `tiles/`, `embeddings/shard_*.npz`, `index.faiss` or Qdrant `summary.json`, `metadata.npz`, and `articles.json`.

## Read or Run

- Read [workflows.md](references/workflows.md) for end-to-end and stage-by-stage recipes.
- Read [config-and-data-formats.md](references/config-and-data-formats.md) for `pixelrag.yaml`, source adapters, chunk manifests, embeddings, and index layouts.
- Read [cli-reference.md](references/cli-reference.md) for flags and command selection.
- Read [troubleshooting.md](references/troubleshooting.md) for stale tiles, article IDs, Qdrant modes, GPU/model issues, and local-source surprises.
- Run [pixelrag_tiny_index_config.py](scripts/pixelrag_tiny_index_config.py) to generate a tiny local-source config without downloading models.

## Common Routes

| Request | Action |
| --- | --- |
| "Index this folder of PDFs/Markdown/images" | Generate a local-source `pixelrag.yaml`; use `pixelrag index build --device auto` for small runs or CUDA for production. |
| "Use Qdrant instead of FAISS" | Set `index.backend: qdrant` and provide URL/collection/client/quantization config as needed. |
| "Re-run after source files changed" | Trust the source-stamped tile manifests; use `--force` only for a clean rebuild. |
| "Department-filter search" | Preserve subdirectory layout under the local source; `articles.json` stores the first subdirectory as `department`. |
| "I already have embeddings" | Use `pixelrag build-index build --embeddings-dir ... --output-dir ...`. |
| "Now query this index" | Route to `../serve-search/SKILL.md`. |

## Validation Checklist

- `pixelrag index build --help` lists `--device {auto,cpu,mps,cuda}`.
- Local source only includes `.pdf`, `.html`, `.htm`, `.png`, `.jpg`, `.jpeg`, `.md`, and `.txt`.
- Wide tiles are chunked into columns no wider than 875 px and rows of 1024 px where applicable.
- `article_id` is propagated into `chunks.json` and embedding metadata.
- `articles.json` titles, URLs/paths, and department fields match the source set.
- Qdrant `append` and `recreate` are explicit choices, never accidental overwrites.
