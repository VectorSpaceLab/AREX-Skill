# Troubleshooting Index Updates and Serving

## Install and import failures

Symptoms:

- `ModuleNotFoundError: No module named 'colbert'`.
- `ModuleNotFoundError: No module named 'flask'` or `dotenv`.
- `ImportError` from PyTorch or optional runtime packages.

Actions:

- Confirm the environment has `colbert-ai` installed and imports `colbert`.
- Install server-only dependencies such as `flask` only when serving is needed.
- Keep helper scripts import-lazy so `--help` works even before ColBERT or Flask are installed.
- Do not hide import failures inside a broad `except`; return a clear server JSON error or fail a CLI command loudly.

## Backend and device failures

Symptoms:

- CUDA unavailable during `IndexUpdater.add(...)`.
- PyTorch loads but encoding passages fails.
- CPU mmap behavior differs from GPU search behavior.

Actions:

- Remember that CPU import inspection is verified, but passage encoding for add/update workflows is usually GPU-oriented.
- Use the same checkpoint/config family used for indexing.
- For CPU search, consider `ColBERTConfig(load_index_with_mmap=True)` only for read-only search; do not assume it makes update/persist workflows cheap or fully CPU-friendly.

## Invalid pids

Symptoms:

- `ValueError("Invalid PIDs", invalid_pids)` from `remove(...)`.
- Removed passages still appear after reload.

Actions:

- Validate every pid is an integer in `0 <= pid < len(searcher.ranker.doclens)`.
- Ensure the pid refers to the same collection/index version the searcher loaded.
- Distinguish in-memory remove from persisted remove: reload sees the old disk state until `persist_to_disk()` completes.

## Add failures

Symptoms:

- `ValueError: No checkpoint was provided at IndexUpdater initialization.`
- New passages never appear in results.
- New pids are unexpected.

Actions:

- Pass `checkpoint=...` to `IndexUpdater(config, searcher, checkpoint=...)` for any `add(...)` workflow.
- Use non-empty passage strings and the same doc max length/config assumptions as the index.
- Expect new pids to start at the current number of doclens entries, not at a caller-supplied id.
- Search with a query that should strongly match the added passage before deciding the add failed.

## Persist and artifact mismatch failures

Symptoms:

- Fresh `Searcher` fails after persistence.
- `metadata.json` values disagree with chunk files.
- `doclens`, `codes`, `residuals`, or `ivf.pid.pt` appear inconsistent.
- A crash or full disk occurred during `persist_to_disk()`.

Actions:

- Restore from an index backup or retry on a fresh copy; do not keep serving a half-written directory.
- Check `metadata.json`, each `N.metadata.json`, `doclens.N.json`, `N.codes.pt`, `N.residuals.pt`, and `ivf.pid.pt` together.
- Removed pids intentionally leave zero doclens slots while embeddings are removed and offsets are adjusted.
- Added passages may create new chunk files when the previous last chunk is full.
- If coalescing, write to a separate output directory and validate the output with a fresh `Searcher` before replacing anything.

## Coalesce failures

Symptoms:

- Missing `plan.json`, `metadata.json`, or chunk files.
- Very high memory use while coalescing residuals.
- Output has `num_chunks=1` but search fails.

Actions:

- Coalescing expects a complete ColBERT index directory, not just selected tensors.
- Ensure disk space and RAM can hold the combined codes/residuals tensors.
- Check that `metadata["num_embeddings"]`, `metadata["config"]["dim"]`, and `metadata["config"]["nbits"]` match tensor shapes.
- Compare doclens/codes/residuals between source and output before switching serving traffic.

## Server configuration failures

Symptoms:

- Server crashes on import or before `--help`.
- Missing `INDEX_ROOT`, `INDEX_NAME`, or `PORT` creates a traceback.
- `/api/search` returns HTML errors instead of JSON.

Actions:

- Use a lazy app factory and create `Searcher` only after CLI/env validation.
- Require `--index-name` or `INDEX_NAME`; pass `--index-root` or `INDEX_ROOT` when the index is outside the default ColBERT run layout.
- Default `PORT` to a sensible integer such as 8893 and validate it.
- Return JSON errors for missing query text, invalid `k`, and initialization failures.

## k cap and empty results

Symptoms:

- Caller asks for `k=1000` and receives only 100 results.
- Probability normalization divides by zero.

Actions:

- The lightweight server pattern caps API `k` at 100. Document this as a product choice.
- Validate `k >= 1`; clamp `k` to 100 for serving.
- If the searcher returns no pids, return an empty `topk` list and avoid probability normalization.
