# Index and Search Workflows

This reference gives copy-editable ColBERT workflows for common indexing and retrieval tasks. Replace placeholder paths with user-owned paths and avoid assuming any repository checkout layout.

## Preflight checklist

1. Confirm imports: `python -c "import colbert; print(colbert.__file__)"`.
2. Confirm the checkpoint is a local path, or accept that a model name may trigger a download.
3. Validate collection, query, and ranking TSV files with `scripts/validate_colbert_inputs.py`.
4. Pick a stable `root`, `experiment`, and `index_name`.
5. Decide whether an existing index should fail, be reused, be resumed, or be overwritten.
6. Confirm GPU availability and disk capacity before realistic indexing.

## Collection and query TSV basics

Minimal collection TSV:

```text
0	first passage text
1	second passage text
2	third passage text
```

ColBERT's collection loader expects `pid` values to match the zero-based line offset. It can also accept a header row beginning with `id`, and collection rows may include a third title column that is prepended internally as title plus passage.

Minimal query TSV:

```text
1	what is late interaction?
2	how does residual compression work?
```

Query IDs must be unique integers and query text should be non-empty. Extra columns after the query text may be ignored by loaders, so validate before running expensive jobs.

## Build an index

```python
from colbert import Indexer
from colbert.infra import Run, RunConfig, ColBERTConfig


def build_index(checkpoint, collection, experiment_root, experiment, index_name):
    with Run().context(RunConfig(nranks=1, experiment=experiment)):
        config = ColBERTConfig(
            root=experiment_root,
            nbits=2,
            doc_maxlen=180,
        )
        indexer = Indexer(checkpoint=checkpoint, config=config)
        return indexer.index(
            name=index_name,
            collection=collection,
            overwrite=False,
        )


if __name__ == "__main__":
    path = build_index(
        checkpoint="/path/to/local/checkpoint",
        collection="/path/to/collection.tsv",
        experiment_root="/path/to/experiments",
        experiment="demo",
        index_name="collection.nbits=2",
    )
    print(f"Index written to: {path}")
```

Expected default location:

```text
/path/to/experiments/demo/indexes/collection.nbits=2/
```

For automation, print and persist the returned index path; it is the safest way to avoid later `root`/`experiment` mistakes.

## Reuse, overwrite, or resume

Use ColBERT's explicit policy rather than manually deleting directories:

```python
indexer.index(name="collection.nbits=2", collection=collection, overwrite="reuse")
```

Recommended meanings:

- First build: `overwrite=False` so accidental collisions fail early.
- Known-good existing index: `overwrite='reuse'` so indexing is skipped when the directory exists.
- Intentional rebuild: `overwrite=True` or `'force_silent_overwrite'`.
- Interrupted compatible build: `overwrite='resume'`.

`True` waits before deletion; `'force_silent_overwrite'` avoids the wait and should be used only when automation has already confirmed the target path is safe to delete.

## Load an existing index by root and experiment

```python
from colbert import Searcher
from colbert.infra import Run, RunConfig, ColBERTConfig

with Run().context(RunConfig(nranks=1, experiment="demo")):
    config = ColBERTConfig(root="/path/to/experiments")
    searcher = Searcher(index="collection.nbits=2", config=config)
```

This expects:

```text
/path/to/experiments/demo/indexes/collection.nbits=2/
```

Use the same `experiment` that was active during indexing unless you pass `index_root` explicitly.

## Load an index with explicit index_root

Use this when the index is not under `root/experiment/indexes/` or when the user gives a directory containing indexes:

```python
from colbert import Searcher
from colbert.infra import ColBERTConfig

searcher = Searcher(
    index="collection.nbits=2",
    index_root="/path/to/index-root",
    config=ColBERTConfig(),
    collection="/path/to/collection.tsv",
)
```

This expects:

```text
/path/to/index-root/collection.nbits=2/
```

If the user gives the full index directory, split it into parent and basename:

```python
index_root = "/path/to/index-root"
index_name = "collection.nbits=2"
```

Do not pass the full index directory as `root`; that makes ColBERT look for another nested `experiment/indexes/index_name` path.

## Single-query search

```python
pids, ranks, scores = searcher.search("what is late interaction?", k=10)

for pid, rank, score in zip(pids, ranks, scores):
    passage = searcher.collection[pid]
    print(f"rank={rank} pid={pid} score={score:.3f}\t{passage}")
```

If `searcher.collection[pid]` fails, instantiate `Searcher` with `collection="/path/to/collection.tsv"` so passage lookup uses the intended collection.

## Batch search from a TSV

```python
from colbert.data import Queries

queries = Queries("/path/to/queries.tsv")
ranking = searcher.search_all(queries, k=100)
output_path = ranking.save("ranking.tsv")
print(output_path)
```

`ranking.save("ranking.tsv")` writes into the active `Run` output path when the path is relative. To write to a precise location, pass an absolute output path or use the returned `output_path`.

## Batch search from an in-memory dictionary

```python
from colbert.data import Queries

queries = Queries(data={
    101: "what is late interaction?",
    102: "how does ColBERT compression work?",
})
ranking = searcher.search_all(queries, k=20)
print(ranking.tolist()[:5])
```

`ranking.tolist()` contains rows like:

```python
(qid, pid, rank, score)
```

## Restrict candidates with pids or qid_to_pids

For one query:

```python
allowed_pids = [10, 42, 77]
pids, ranks, scores = searcher.search("targeted query", k=3, pids=allowed_pids)
```

For batch search:

```python
queries = Queries(data={1: "first query", 2: "second query"})
qid_to_pids = {1: [10, 42], 2: [77, 80, 81]}
ranking = searcher.search_all(queries, k=2, qid_to_pids=qid_to_pids)
```

Every query ID must have a key in `qid_to_pids`. Use `None` for a query that should be unrestricted. Invalid or missing keys can fail before ranking or accidentally exclude all candidates.

## Save and inspect ranking output

ColBERT ranking rows are tab-separated. For unannotated rankings produced by `Searcher.search_all`, the common shape is:

```text
qid	pid	rank	score
```

Some documentation summarizes top-k ranking as `qid<TAB>pid<TAB>rank`; `Ranking.save()` preserves the tuple shape produced by the ranking object, and search output includes scores.

Validate saved output when downstream tools are strict:

```bash
python scripts/validate_colbert_inputs.py --ranking /path/to/ranking.tsv
```

## Tune search speed and recall

Default dynamic settings are often a good first pass:

```python
config = ColBERTConfig(root="/path/to/experiments")
searcher = Searcher(index="collection.nbits=2", config=config)
```

For more recall at higher cost:

```python
config = ColBERTConfig(
    root="/path/to/experiments",
    ncells=4,
    centroid_score_threshold=0.4,
    ndocs=4096,
)
```

For lower latency at possible recall cost:

```python
config = ColBERTConfig(
    root="/path/to/experiments",
    ncells=1,
    centroid_score_threshold=0.5,
    ndocs=256,
)
```

Keep `k <= ndocs`. For `k > 100`, ColBERT defaults to `ndocs=max(k * 4, 4096)` when `ndocs` is omitted.

## CPU-only search with memory mapping

Before starting Python on a GPU host:

```bash
CUDA_VISIBLE_DEVICES="" python search_script.py
```

Then configure search:

```python
config = ColBERTConfig(
    root="/path/to/experiments",
    load_index_with_mmap=True,
)
searcher = Searcher(index="collection.nbits=2", config=config)
```

`load_index_with_mmap=True` is only valid when ColBERT sees no GPU. It can reduce memory pressure for CPU search but is not a substitute for GPU indexing on large collections.

## Minimal reusable function pair

```python
from colbert import Indexer, Searcher
from colbert.infra import Run, RunConfig, ColBERTConfig


def index_collection(checkpoint, collection, root, experiment, index_name, overwrite=False):
    with Run().context(RunConfig(nranks=1, experiment=experiment)):
        config = ColBERTConfig(root=root, nbits=2)
        return Indexer(checkpoint, config=config).index(index_name, collection, overwrite=overwrite)


def search_queries(root, experiment, index_name, queries, output_path, k=100, collection=None):
    with Run().context(RunConfig(nranks=1, experiment=experiment)):
        config = ColBERTConfig(root=root)
        searcher = Searcher(index=index_name, collection=collection, config=config)
        ranking = searcher.search_all(queries, k=k)
        return ranking.save(output_path)
```

Keep `Searcher` inside the run context for scripts that immediately search and save ranking output, especially when using relative ranking paths.

## Native recipe adaptation

A safe adaptation of ColBERT's end-to-end examples is:

1. Build the index with `RunConfig(nranks=1)` and `ColBERTConfig(root=..., nbits=1 or 2, doc_maxlen=180)`.
2. Initialize `Searcher(index=..., config=ColBERTConfig(root=...))` inside the same `experiment` context.
3. For single-query checks, call `searcher.search(question, k=5)` and inspect `searcher.collection[pid]`.
4. For batch checks, create `Queries(...)`, call `searcher.search_all(...)`, and save with an absolute output path.
5. Run native examples/tests only when the user supplies the checkpoint, collection, network/GPU permission, and expected labels.
