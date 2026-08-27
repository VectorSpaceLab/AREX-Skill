# Indexing and Search API Reference

This reference covers the public ColBERT APIs most often needed to build indexes, load indexes, search, tune retrieval, and save rankings.

## Imports

```python
from colbert import Indexer, Searcher
from colbert.data import Collection, Queries, Ranking
from colbert.infra import Run, RunConfig, ColBERTConfig
```

If imports fail, first verify the environment has `colbert-ai` installed and that `python -c "import colbert; print(colbert.__file__)"` resolves to the intended environment.

## Run context and configuration

`Run().context(RunConfig(...))` controls run-level paths and resources. `Indexer` and `Searcher` merge explicit `ColBERTConfig` values with the active `Run().config`, so keep the run context consistent between indexing, search, and ranking save.

Important fields:

| Field | Typical use |
| --- | --- |
| `root` | Top-level experiment directory, commonly a user-owned experiments directory. |
| `experiment` | Experiment namespace under `root`; set in `RunConfig`, not only in `ColBERTConfig`. |
| `index_root` | Optional direct directory containing indexes; otherwise ColBERT derives `root/experiment/indexes/`. |
| `nranks` | Number of parallel ranks/processes. Use `1` for minimal local templates. |
| `gpus` | GPU allocation through run configuration when the host supports it. |
| `doc_maxlen` | Passage truncation length; README recipes commonly use `180`. |
| `query_maxlen` | Query truncation length; default is usually sufficient unless full-length query behavior is required. |
| `nbits` | Residual compression bits; README indexing recipe uses `2`. |
| `index_bsize` | Indexing batch size; prefer this over `bsize` for indexing. |
| `ncells` | Number of centroid cells searched; omit to let ColBERT choose based on `k`. |
| `centroid_score_threshold` | Candidate pruning threshold; omit to let ColBERT choose based on `k`. |
| `ndocs` | Candidate document count; omit to let ColBERT choose based on `k`. |
| `load_index_with_mmap` | CPU-only memory-mapped index loading; invalid when GPUs are visible. |

Index path resolution:

- Default index root: `root/experiment/indexes/`.
- Default full index path: `index_root/index_name`.
- `Indexer.index(name=...)` sets `index_name=name` and returns the created index path.
- `Searcher(index=..., config=...)` looks for `index` below `config.index_root` if set, otherwise below `config.root/config.experiment/indexes/` as resolved through the active `Run` context.
- `Searcher(index=..., index_root=...)` overrides the directory used to find the index directory.

## Indexer

Verified signature:

```python
Indexer(checkpoint, config=None, verbose: int = 3)
Indexer.index(name, collection, overwrite=False)
Indexer.get_index()
Indexer.erase(force_silent: bool = False)
```

Basic pattern:

```python
with Run().context(RunConfig(nranks=1, experiment="my-experiment")):
    config = ColBERTConfig(root="/path/to/experiments", nbits=2, doc_maxlen=180)
    indexer = Indexer(checkpoint="/path/to/checkpoint", config=config)
    index_path = indexer.index(
        name="my-index.nbits=2",
        collection="/path/to/collection.tsv",
        overwrite=False,
    )
    print(index_path)
```

`collection` is commonly a TSV path accepted by `Collection.cast`. ColBERT indexing loads and samples the collection, creates an index plan, trains centroids, writes residual codes, and finalizes metadata/IVF files.

### Overwrite policy

`overwrite` accepts `False`, `True`, `'reuse'`, `'resume'`, and `'force_silent_overwrite'`.

- `False`: fail if the target index path already exists.
- `True`: delete existing ColBERT index files after an interactive delay, then rebuild.
- `'force_silent_overwrite'`: delete existing ColBERT index files without the delay.
- `'reuse'`: if the index directory exists, skip rebuilding and return the existing path.
- `'resume'`: configure resume mode for an interrupted compatible indexing workflow.

## Searcher

Verified signature:

```python
Searcher(index, checkpoint=None, collection=None, config=None, index_root=None, verbose: int = 3)
Searcher.search(text, k=10, filter_fn=None, full_length_search=False, pids=None)
Searcher.search_all(queries, k=10, filter_fn=None, full_length_search=False, qid_to_pids=None)
Searcher.dense_search(Q, k=10, filter_fn=None, pids=None)
Searcher.encode(text, full_length_search=False)
```

Open an index with the default layout:

```python
with Run().context(RunConfig(nranks=1, experiment="my-experiment")):
    config = ColBERTConfig(root="/path/to/experiments")
    searcher = Searcher(index="my-index.nbits=2", config=config)
```

Open an index outside the default layout:

```python
searcher = Searcher(
    index="my-index.nbits=2",
    index_root="/path/to/directory/containing/indexes",
    config=ColBERTConfig(),
    collection="/path/to/collection.tsv",
)
```

`checkpoint` is optional when the index metadata records a valid checkpoint. Pass it explicitly if the metadata points to a moved checkpoint or when intentionally overriding the recorded checkpoint.

## Collection, Queries, and Ranking

Verified constructors:

```python
Collection(path=None, data=None)
Queries(path=None, data=None)
Ranking(path=None, data=None, metrics=None, provenance=None)
```

`Collection.cast` accepts a TSV path, a list of passages, or a `Collection`. `Queries.cast` accepts a TSV path, a dictionary, a list, or a `Queries`. `Ranking.cast` accepts a ranking TSV path, a dictionary/list data object, or a `Ranking`.

For single-query search:

```python
pids, ranks, scores = searcher.search("what is late interaction?", k=10)
for pid, rank, score in zip(pids, ranks, scores):
    passage = searcher.collection[pid]
    print(rank, pid, score, passage)
```

For batch search:

```python
queries = Queries("/path/to/queries.tsv")
ranking = searcher.search_all(queries, k=100)
output_path = ranking.save("my-ranking.tsv")
print(output_path)
```

`Ranking.save(path)` writes rows from `ranking.flat_ranking` plus a `.meta` file. Because it uses `Run().open`, relative paths are written under the active run path. Use an absolute path or print the returned value when the destination matters.

## Search hyperparameter defaults

When `ncells`, `centroid_score_threshold`, and `ndocs` are omitted, `Searcher.dense_search()` fills them from `k`:

| `k` range | `ncells` | `centroid_score_threshold` | `ndocs` |
| --- | ---: | ---: | ---: |
| `k <= 10` | `1` | `0.5` | `256` |
| `10 < k <= 100` | `2` | `0.45` | `1024` |
| `k > 100` | `4` | `0.4` | `max(k * 4, 4096)` |

Larger `ncells` and `ndocs` usually improve recall and increase latency/memory. Keep `k <= ndocs` when setting `ndocs` manually.

## Filtering and restricted search

- `filter_fn` can be passed to `search`, `search_all`, or `dense_search` and is forwarded to the ranker.
- `pids` restricts one dense search to candidate passage IDs.
- `qid_to_pids` restricts `search_all` per query; its keys must cover the query IDs being searched.
- `full_length_search=True` asks the query encoder not to use the normal query-length truncation path.

## CPU/GPU behavior

- Practical indexing normally needs CUDA/GPU; use CPU only for tiny smoke checks.
- `Searcher` uses GPU when visible GPUs are available; otherwise it runs on CPU.
- `load_index_with_mmap=True` is CPU-only. If GPUs are visible, `Searcher` raises `ValueError("Memory-mapped index can only be used with CPU!")`.
- To force CPU-only search on a GPU host before Python starts, use `CUDA_VISIBLE_DEVICES=""`.

## Checkpoint source behavior

A checkpoint may be a local path or a model name resolvable by model-loading dependencies. Model names can trigger network downloads if not cached. Prefer explicit local checkpoint paths for reproducible production scripts.
