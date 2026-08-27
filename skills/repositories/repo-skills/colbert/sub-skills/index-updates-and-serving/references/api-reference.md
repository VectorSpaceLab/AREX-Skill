# API Reference for Index Updates and Serving

## Public imports and constructors

Use public ColBERT imports in user-facing code:

```python
from colbert import Searcher, IndexUpdater
from colbert.infra import Run, RunConfig, ColBERTConfig
```

Verified package facts for this skill:

- Distribution: `colbert-ai` 0.2.22.
- Import package: `colbert`.
- Verified imports include `colbert`, `colbert.infra`, `colbert.data`, `colbert.modeling.checkpoint`, `utility`, and `baleen`.
- CPU import inspection works. Practical passage encoding for `IndexUpdater.add(...)` normally needs a working PyTorch backend and is usually GPU-oriented.

Important verified signatures:

```python
Searcher(index, checkpoint=None, collection=None, config=None, index_root=None, verbose=3)
IndexUpdater(config, searcher, checkpoint=None)
ColBERTConfig(...)
Run().context(RunConfig(...))
```

## Searcher for an existing index

Load the same index identity used during indexing. Two common forms are:

```python
config = ColBERTConfig(root="/experiments", experiment="demo")
searcher = Searcher(index="my-index", checkpoint="checkpoint-or-model", collection="collection.tsv", config=config)
```

or, when the index directory is managed outside the default run layout:

```python
config = ColBERTConfig(root="/experiments", experiment="demo")
searcher = Searcher(index="my-index", checkpoint="checkpoint-or-model", collection="collection.tsv", config=config, index_root="/indexes")
```

The `searcher.index` attribute resolves to the concrete index directory used by `IndexUpdater` for IVF, metadata, doclens, codes, and residual files.

## IndexUpdater lifecycle

`IndexUpdater(config, searcher, checkpoint=None)` mutates the `Searcher` it is given.

- `remove(pids)` accepts a list of integer pids and removes those pids from the in-memory IVF used by the current searcher.
- `add(passages)` accepts a list of passage strings, encodes them with the checkpoint, appends them to the current searcher, and returns the new pid list.
- `persist_to_disk()` writes all previously tracked additions and removals to the index directory on disk and updates metadata plus `ivf.pid.pt`.

Adding requires a checkpoint at `IndexUpdater` initialization. Removing can be initialized without a checkpoint, but most practical workflows pass the same checkpoint that was used to create or search the index so the workflow can support both add and remove.

## In-memory versus persisted changes

Before `persist_to_disk()`:

- The current `searcher` reflects additions/removals.
- A newly constructed `Searcher` for the same index reads the original on-disk artifacts and does not see the changes.
- Added passages are assigned pids starting at the current `len(searcher.ranker.doclens)`.

After `persist_to_disk()`:

- Removed pids have zero doclens in their chunk and their embeddings are removed from the chunk tensors.
- Added passages are appended to the last chunk if capacity allows, otherwise new chunk files are created.
- Global and chunk metadata are rewritten.
- `ivf.pid.pt` is written so subsequent searchers load the updated pid mapping.
- A fresh `Searcher` should be created to validate the on-disk state.

## Return shapes for serving

`Searcher.search(query, k=...)` returns parallel sequences:

```python
pids, ranks, scores = searcher.search("query text", k=10)
```

A lightweight API can expose JSON entries like:

```json
{
  "query": "Who won the 2022 FIFA world cup?",
  "topk": [
    {"text": "...", "pid": 12, "rank": 1, "score": 14.2, "prob": 0.41}
  ]
}
```

The public ColBERT server example caps API results at 100. Preserve that cap unless the caller explicitly redesigns candidate retrieval, payload size, timeout, and cache behavior.
