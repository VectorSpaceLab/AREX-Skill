# Data API Reference

ColBERT's data wrappers are intentionally small. They load common formats, provide collection-like behavior, and preserve provenance for run metadata.

## `Collection`

Constructor:

```python
Collection(path=None, data=None)
```

Accepted inputs:

- `path="collection.tsv"`: loads TSV passage text.
- `data=["passage zero", "passage one"]`: wraps an in-memory list.
- `Collection.cast(obj)`: accepts a path string, list, or existing `Collection`.

Important behavior:

- Iteration yields passage strings.
- `collection[pid]` indexes the loaded passage list.
- `len(collection)` returns the number of passages.
- `save(new_path)` writes `pid<TAB>content` rows to a new `.tsv` file.
- `save()` asserts the output path ends in `.tsv` and does not already exist.
- JSONL collection loading is not implemented in the wrapper.
- In distributed run contexts, `enumerate_batches(rank=...)` shards chunks across ranks.

Caller guidance:

- Use a normal two-column `collection.tsv` whenever possible.
- Do not rely on `Collection(data=list)` to preserve external PIDs; saving re-enumerates from zero.
- For large files, validate by streaming before constructing full in-memory fixtures.

## `Queries`

Constructor:

```python
Queries(path=None, data=None)
```

Accepted inputs:

- `path="queries.tsv"`: loads TSV queries.
- `path="qas.json"`: loads JSON-lines QA dictionaries when the path ends in `.json`.
- `data={qid: text}`: wraps a dictionary.
- `data={qid: {"question": text, ...}}`: wraps QA dictionaries and keeps full QA data.
- `Queries.cast(obj)`: accepts a path string, dict, list, or existing `Queries`.

Important behavior:

- Iteration yields `(qid, query_text)` pairs.
- `keys()`, `values()`, and `items()` proxy the internal dict.
- `save(new_path)` writes TSV rows and asserts no overwrite.
- `save_qas(new_path)` writes JSON lines with qids injected into QA dictionaries and asserts no overwrite.
- Duplicate qids in QA JSON input are rejected.
- The wrapper checks `.json`, not `.jsonl`, for the QA file branch.

Caller guidance:

- Use `queries.tsv` for search and retrieval tasks.
- Use QA JSON only when a caller specifically needs `Queries.qas()` or an exact-match workflow.
- Validate duplicate qids before loading large files to fail with clearer messages.
- Keep LoTTE `qas.*.jsonl` separate from the `.json` QA shape unless adapting field names.

## `Ranking`

Constructor:

```python
Ranking(path=None, data=None, metrics=None, provenance=None)
```

Accepted inputs:

- `path="ranking.tsv"`: loads tab-separated ranking rows.
- `data=[(qid, pid, rank), ...]` or `data=[(qid, pid, rank, score), ...]`: wraps a flat ranking list.
- `data={qid: [(pid, rank), ...]}` style dictionaries: flattens under qid.
- `Ranking.cast(obj)`: accepts a path string, dict, list, or existing `Ranking`.

Important behavior:

- `load_ranking()` numericizes row values to integers or floats.
- `Ranking.data` groups rows by qid.
- `Ranking.flat_ranking` preserves a flat row list for saving.
- `items()` iterates grouped qid rankings.
- `tolist()` returns flat rows.
- `todict()` returns grouped rankings as a dict.
- `save(new_path)` writes TSV rows and a `new_path.meta` sidecar.
- `save()` requires `tsv` in the final filename's extension segments.

Caller guidance:

- Keep ranks 1-indexed even when a downstream evaluator enumerates row position internally.
- Use four columns when a merge, LoTTE, or score-sensitive workflow follows.
- Confirm sidecar collisions as well as the primary ranking output path before saving.
- If PID or QID types came from JSON strings, normalize before creating ranking rows.

## Related Public APIs

Data objects commonly connect to these verified signatures:

```python
Indexer(checkpoint, config=None, verbose=3)
Searcher(index, checkpoint=None, collection=None, config=None, index_root=None, verbose=3)
Trainer(triples, queries, collection, config=None)
IndexUpdater(config, searcher, checkpoint=None)
```

Use this sub-skill to validate files passed into those APIs. Use the appropriate execution sub-skill for GPU indexing, search, training, or index updates.

## Smoke Checks Without ColBERT Imports

The bundled `scripts/validate_colbert_data.py` validates file contracts without importing ColBERT. This helps in minimal CPU environments, CI, or before expensive GPU runs.

Recommended order:

1. Validate `collection.tsv` and `queries.tsv` for row shape and duplicate IDs.
2. Validate `ranking.tsv` for integer qids/pids and sequential rank per qid.
3. Validate `qrels.tsv` or LoTTE QA JSONL against ranking qids.
4. Run `scripts/evaluate_tiny_ranking.py` for expected metrics.
5. Only then run GPU-backed retrieval or native repository evaluation utilities.
