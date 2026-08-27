# Indexing and Search Troubleshooting

Use this guide to diagnose common ColBERT indexing/search failures without relying on a source checkout.

## Install or import failures

Symptoms:

- `ModuleNotFoundError: No module named 'colbert'`.
- Importing `colbert` works in one shell but not in the script runner.
- `utility`, `baleen`, `ujson`, or model-loading dependencies are missing.

Checks:

```bash
python -c "import sys, colbert; print(sys.executable); print(colbert.__file__)"
```

Fixes:

- Install the `colbert-ai` distribution in the Python environment that runs the script.
- Re-run from the intended virtualenv/conda environment instead of a system Python.
- Install optional/runtime dependencies required by the workflow, especially for ranking metadata and model loading.
- Avoid using local package directories or source checkout paths in production scripts.

## Missing checkpoint files or network downloads

Symptoms:

- `ColBERTConfig.load_from_checkpoint(...)` fails.
- Transformers or Hugging Face errors appear before indexing/search starts.
- A script unexpectedly tries to download model files.

Checks:

```python
from pathlib import Path
checkpoint = Path("/path/to/checkpoint")
print(checkpoint.exists(), checkpoint)
```

Fixes:

- Prefer a local checkpoint path for reproducible runs.
- If using a model name, confirm network access and cache policy.
- If loading an existing index, inspect whether its metadata references a moved checkpoint; pass `Searcher(checkpoint="/new/path", ...)` when necessary.
- Route tokenizer/model compatibility questions to `../modeling-and-tokenization/` when available.

## Missing or wrong index path

Symptoms:

- `ColBERTConfig.load_from_index(self.index)` fails.
- `Searcher(index=...)` looks under the wrong directory.
- An index exists on disk but `Searcher` cannot find it.

Remember the path formula:

```text
index_root = config.index_root or root/experiment/indexes/
full_index_path = index_root/index
```

Fixes:

- If indexing used `root=/runs` and `experiment=demo`, search inside `RunConfig(experiment="demo")` with `ColBERTConfig(root="/runs")`.
- If the full index directory is `/runs/demo/indexes/name`, pass `index_root="/runs/demo/indexes"` and `index="name"`.
- Keep `experiment` identical between indexing and search unless `index_root` is explicit.
- Print and reuse the path returned by `indexer.index(...)` after indexing.

## Root, experiment, and index_root confusion

A frequent mistake is to pass the full index directory as `root`. That makes ColBERT look for another nested `experiment/indexes/index` below it.

Wrong shape:

```python
config = ColBERTConfig(root="/path/to/experiments/demo/indexes/my-index")
Searcher(index="my-index", config=config)
```

Correct shape with root and experiment:

```python
with Run().context(RunConfig(nranks=1, experiment="demo")):
    config = ColBERTConfig(root="/path/to/experiments")
    searcher = Searcher(index="my-index", config=config)
```

Correct shape with explicit index root:

```python
searcher = Searcher(
    index="my-index",
    index_root="/path/to/experiments/demo/indexes",
    config=ColBERTConfig(),
)
```

## Existing index and overwrite semantics

Symptoms:

- Assertion failure with the target index path.
- Rebuild silently skipped or unexpectedly restarts.
- Interrupted indexing leaves partial files.

Policy guide:

- Use `overwrite=False` to fail when the target exists.
- Use `overwrite='reuse'` to skip work when the target exists.
- Use `overwrite='resume'` after an interrupted compatible build.
- Use `overwrite=True` for an intentional rebuild with a deletion delay.
- Use `overwrite='force_silent_overwrite'` only after confirming the target path is safe to delete.

Avoid manually deleting selected files unless you understand the index layout. ColBERT's `Indexer.erase()` deletes ColBERT index artifacts such as `.json` metadata/doclen/plan files and `.pt` files.

## GPU/backend constraints

Symptoms:

- Indexing is extremely slow on CPU.
- CUDA/GPU visibility assertions fail when `RunConfig(gpus=...)` is incompatible with the host.
- Large indexing jobs exhaust memory.

Guidance:

- Practical indexing normally needs CUDA/GPU; use tiny collections only for CPU smoke tests.
- Keep `nranks=1` for local templates; increase only when the runtime environment and GPU allocation are known.
- Set `index_bsize` in `ColBERTConfig` to control indexing batch size; `Indexer.index()` internally sets `bsize=64` and notes that indexing batch size should use `index_bsize`.
- Verify `torch` can see the intended device before launching an expensive job.

## CPU memory-mapped search

Symptoms:

- `ValueError: Memory-mapped index can only be used with CPU!`

Cause:

- `load_index_with_mmap=True` was set while ColBERT detected visible GPUs.

Fix:

```bash
CUDA_VISIBLE_DEVICES="" python search_script.py
```

Then configure:

```python
config = ColBERTConfig(load_index_with_mmap=True, root="/path/to/experiments")
```

Use memory mapping for CPU search memory pressure, not for GPU search.

## Collection TSV format errors

Symptoms:

- Assertions from collection loading about `pid` and line index.
- Indexing fails while loading collection.
- Search results cannot map `pid` back to passage text.

Required shape:

```text
0	first passage
1	second passage
```

Rules:

- First column must be an optional `id` header or an integer equal to the zero-based passage offset.
- Passage text is the second column.
- Optional title is the third column.
- Empty passage text should be fixed before indexing.

Use:

```bash
python scripts/validate_colbert_inputs.py --collection collection.tsv
```

## Query TSV format errors

Symptoms:

- `ValueError` converting query IDs to integers.
- Assertion that a query ID is repeated.
- Batch search retrieves fewer queries than expected.

Required shape:

```text
1	query text
2	another query text
```

Rules:

- Query ID must be an integer.
- Query IDs must be unique.
- Query text must be non-empty.
- Extra columns after the query text can hide malformed tabs; validate when in doubt.

Use:

```bash
python scripts/validate_colbert_inputs.py --queries queries.tsv
```

## Ranking TSV format errors

Symptoms:

- Evaluation scripts reject ranking rows.
- `Ranking(path=...)` fails numeric parsing.
- Saved ranking has an unexpected path.

Common search output shape:

```text
qid	pid	rank	score
```

Rules:

- `qid`, `pid`, and `rank` should be integer-like.
- `rank` should be one-based and positive.
- `score`, when present, should be numeric.
- Ranking rows should not be empty.
- `Ranking.save("relative.tsv")` writes under `Run().path_`; use an absolute path if the exact destination matters.

Use:

```bash
python scripts/validate_colbert_inputs.py --ranking ranking.tsv
```

## Empty or unexpectedly small rankings

Symptoms:

- `searcher.search(...)` returns empty `pids` or fewer than `k` results.
- `Ranking.save(...)` writes no rows or fewer rows than expected.

Checks:

1. Confirm the index was built from the expected non-empty collection.
2. Confirm `k > 0` and `k <= ndocs` if `ndocs` is set.
3. Remove `filter_fn`, `pids`, or `qid_to_pids` restrictions.
4. Increase `ndocs` and possibly `ncells`.
5. Verify query text is non-empty after preprocessing.
6. Confirm the checkpoint used for indexing and search is compatible.

## Invalid qid_to_pids in batch search

Symptoms:

- `KeyError` during `search_all`.
- Batch search returns empty results for specific queries.
- Candidate restrictions appear to apply to the wrong query.

Fixes:

- Ensure every `Queries` key appears in `qid_to_pids`.
- Use integer keys if query IDs were loaded as integers.
- Use values that are lists/iterables of valid passage IDs, or `None` for unrestricted queries.
- Validate that restricted pids exist in the indexed collection.

## Search quality or latency is poor

Quality-first configuration:

```python
ColBERTConfig(ncells=4, centroid_score_threshold=0.4, ndocs=4096)
```

Latency-first configuration:

```python
ColBERTConfig(ncells=1, centroid_score_threshold=0.5, ndocs=256)
```

Defaults depend on `k` if these values are omitted:

- `k <= 10`: `ncells=1`, `centroid_score_threshold=0.5`, `ndocs=256`.
- `10 < k <= 100`: `ncells=2`, `centroid_score_threshold=0.45`, `ndocs=1024`.
- `k > 100`: `ncells=4`, `centroid_score_threshold=0.4`, `ndocs=max(k * 4, 4096)`.

## Output file not where expected

Symptoms:

- `ranking.save("ranking.tsv")` succeeds but the file is not in the shell working directory.

Cause:

- `Ranking.save()` uses `Run().open`, which resolves relative paths below the active run output directory.

Fixes:

- Print and use the returned output path.
- Pass an absolute output path.
- Set `RunConfig(root=..., experiment=...)` intentionally so run outputs are predictable.

## API misuse checklist

- Use `Indexer(checkpoint=..., config=...)`, then `indexer.index(name=..., collection=..., overwrite=...)`.
- Use `Searcher(index=..., config=..., index_root=...)`, not `Searcher(path_to_full_index_dir)` unless the basename is actually resolvable through `index_root`.
- Pass `collection=...` to `Searcher` when passage lookup is needed and index metadata does not provide a collection path.
- Pass `Queries(...)` or a compatible dictionary/list to `search_all`, not a raw file handle.
- Keep indexing/search inside intentional `Run().context(...)` blocks when using relative paths or saving rankings.
