# Serve/Search Troubleshooting

## `/health` works but `/status` fails

The FastAPI app is running, but the index/backend did not load correctly. Check:

- `--index-dir` points at the directory with `summary.json` and backend files.
- FAISS mode has `index.faiss` and `metadata.npz`.
- Qdrant mode has a reachable Qdrant endpoint and matching collection.
- `--articles-json` exists if hits need URLs/titles/departments.

## Server is slow to start

Large FAISS indexes may take minutes to load. Use `PIXELRAG_INDEX_MMAP=1` for large read-only FAISS indexes when memory mapping is acceptable. Query encoder model loading can also be slow, especially on CPU.

## Search times out or returns empty in benchmarks

- Confirm `/status` reports the expected vector count.
- Increase the client timeout when using on-demand rendering; benchmark code reads `PIXELRAG_RETRIEVAL_TIMEOUT`.
- Check `nprobe`; too low can hurt recall, too high can slow queries.
- Ensure the query instruction matches the index condition used when building/reproducing results.

## Department filter errors

- `400`: the index has no department metadata.
- `404`: requested department is unknown; call `/departments` to list available values.
- Empty department names are valid for root-level local files but are not usually useful as a filter.

## `Do not mix pre-computed embeddings...`

A `/search` request may use text/image queries or embedding queries, but not both in the same batch. Split mixed-mode queries into separate requests.

## Tile images are missing

- Check `--tiles-dir` points at the tile root used by the index.
- Use `/tile/{article_id}/{tile_index}/{chunk_index}` rather than absolute file paths.
- If no materialized tile corpus exists, use `--render-on-demand` only for Kiwix-backed indexes.
- Ensure `metadata.npz` chunk coordinates match the tile/chunk files produced during indexing.

## Qdrant payload errors

Rebuild or repair the collection so every point has `article_id`, `tile_index`, `chunk_index`, `y_offset`, and `tile_height` payload fields. PixelRAG's backend contract tests assume those fields are present and integer-convertible.

## CUDA query encoder fails

Run a tiny torch CUDA allocation check in the same environment. If CUDA is unavailable, start with `--device cpu` to prove the index/backend path, then fix torch/CUDA wheel and driver compatibility before claiming GPU serving.

## Agent integration returns too much data

For chat agents, use small `n_docs` and `include_images: false` unless the reader needs images inline. Fetch specific tile images by coordinate only after selecting relevant hits.
