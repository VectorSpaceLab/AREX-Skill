# Index-Build Troubleshooting

## Stage is not installed

The umbrella CLI lazily imports stage modules. If `pixelrag index` or `pixelrag serve` says a stage is not installed, install the narrow extra:

```bash
pip install 'pixelrag[index]'
pip install 'pixelrag[serve]'
pip install 'pixelrag[qdrant]'
```

Avoid `pixelrag[all]` unless the user truly needs every optional workflow.

## Model download or embedding is too slow

`Qwen/Qwen3-VL-Embedding-2B` is large. CPU embedding is useful for small smoke tests, but production indexing should use CUDA or Apple MPS where available. Use `--limit` first and keep data/model downloads explicit.

## Wide images or PDFs are skipped by the embedder

Current chunking splits wide tiles into width columns at or below 875 px and height rows of 1024 px. If chunks are missing:

- Run `pixelrag chunk --shard-dir <tiles> --force`.
- Inspect `chunks.json` widths and file names.
- Confirm the source tile exists and Pillow can open it.

## Wrong document appears under an article ID after rerun

Do not relabel existing tile directories. The orchestrator stamps source identity into manifests and removes/re-renders stale directories when the source set changes. If output is confusing, run a clean rebuild with `--force`.

## Non-numeric tile directory names create unstable IDs

Modern manifests carry `article_id`. Legacy non-numeric names fall back to a stable SHA1-derived ID, not Python's salted `hash()`. Prefer orchestrator-created numeric stems for new indexes.

## Local source misses files

`local` only includes `.pdf`, `.html`, `.htm`, `.png`, `.jpg`, `.jpeg`, `.md`, and `.txt`. CSV, DOCX, and other formats must be converted first.

## Department filter is empty

Department comes from the first subdirectory under the local source root. Files at the root have no department, and web URLs are outside the root. Rebuild after organizing files into subdirectories.

## Qdrant collection conflicts

If a collection exists:

- Use `--append` only when vectors and payload schema match.
- Use `--recreate` only after confirming destructive replacement is acceptable.
- Provide `--qdrant-client-config` for non-default local/Cloud options.
- Keep the collection name aligned between build and serve.

## FAISS index build memory pressure

Large IVF indexes need training samples and memory. For tiny smoke tests, PixelRAG auto-adjusts `nlist` based on vector count in the orchestrator. For large builds, set `nlist`, `nprobe`, and GPU training deliberately.
