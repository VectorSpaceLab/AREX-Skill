# API Reference: Persisted Indexing and Search

This reference covers RAGatouille 0.0.9post2 APIs for persisted indexes through `ragatouille.RAGPretrainedModel`. It intentionally excludes in-memory `rerank`, `encode`, and `search_encoded_docs` workflows.

## Imports and Compatibility

```python
from ragatouille import RAGPretrainedModel
```

- The package imports only with a legacy-compatible LangChain stack that still exposes `langchain.retrievers.document_compressors.base`.
- `fast-pytorch-kmeans` can require `psutil` at import/runtime through the indexing path.
- Avoid using model download, GPU, training, or indexing as a smoke test unless explicitly allowed.

## Constructors

### `RAGPretrainedModel.from_pretrained`

Verified signature:

```python
RAGPretrainedModel.from_pretrained(
    pretrained_model_name_or_path: str | pathlib.Path,
    n_gpu: int = -1,
    verbose: int = 1,
    index_root: str | None = None,
)
```

Use this when you have a Hugging Face model id or local ColBERT checkpoint and need to create/search indexes. `index_root` controls where new indexes are persisted; when omitted, RAGatouille uses `.ragatouille/`. Internally the ColBERT run root becomes `index_root`, experiment becomes `colbert`, and an index named `my_index` is stored under:

```text
<index_root>/colbert/indexes/my_index/
```

`n_gpu=-1` means auto-select available GPUs, or use a single rank when CUDA devices are unavailable.

### `RAGPretrainedModel.from_index`

Verified signature:

```python
RAGPretrainedModel.from_index(
    index_path: str | pathlib.Path,
    n_gpu: int = -1,
    verbose: int = 1,
)
```

Use this when an index already exists and should provide the model configuration and checkpoint information. The `index_path` must point at the concrete index directory, for example `.ragatouille/colbert/indexes/Miyazaki/`, not just the root. Loading expects persisted RAGatouille/ColBERT files such as `metadata.json`, `collection.json`, and `pid_docid_map.json`.

## Index Creation

Verified signature:

```python
RAG.index(
    collection: list[str],
    document_ids = None,
    document_metadatas: list[dict] | None = None,
    index_name: str | None = None,
    overwrite_index: bool | str = True,
    max_document_length: int = 256,
    split_documents: bool = True,
    document_splitter_fn = llama_index_sentence_splitter,
    preprocessing_fn = None,
    bsize: int = 32,
    use_faiss: bool = False,
)
```

Key behavior:

- `collection` is a list of source document strings.
- `document_ids` is optional. When omitted, UUID strings are generated.
- Provided `document_ids` must have the same length as `collection`, be unique, contain no empty/whitespace-only strings, and all share the same Python type.
- `document_metadatas`, when provided, must have the same length as `collection`. It is stored as a `docid_metadata_map` keyed by document id.
- `split_documents=True` enables `document_splitter_fn`; the default uses LlamaIndex `SentenceSplitter` with `chunk_size=max_document_length` and chunk overlap capped at 64.
- `split_documents=False` sets `document_splitter_fn=None`, preserving one passage per input document unless preprocessing changes it.
- `preprocessing_fn` may be a callable or list of callables applied by `CorpusProcessor` after splitting.
- `index_name=None` falls back to a checkpoint-derived name; prefer an explicit stable `index_name`.
- `overwrite_index` is passed to ColBERT as `overwrite`; the implementation commonly uses booleans or ColBERT overwrite strings such as `reuse` or `force_silent_overwrite` in internal update paths.
- `bsize` sets indexing batch size.
- `use_faiss=False` uses RAGatouille's PyTorch k-means replacement for smaller collections when possible; set `use_faiss=True` to force FAISS behavior.

Return value: a string path to the created index directory.

## Persisted Index Files

RAGatouille writes these files inside each index directory:

- `collection.json`: list of indexed passages/chunks.
- `pid_docid_map.json`: mapping from passage id integer to original `document_id`. JSON object keys are strings on disk and converted back to integers on load.
- `docid_metadata_map.json`: optional mapping from `document_id` to metadata dictionary.
- `metadata.json`: ColBERT metadata plus a `RAGatouille.index_config` section recording index metadata such as `index_type` and `index_name`.

Document splitting means several passage ids can point to one `document_id`.

## Search

Verified signature:

```python
RAG.search(
    query: str | list[str],
    index_name: str | None = None,
    k: int = 10,
    force_fast: bool = False,
    zero_index_ranks: bool = False,
    doc_ids: list[str] | None = None,
    **kwargs,
)
```

Key behavior:

- Search requires a model instance that has already run `index(...)` or was created with `from_index(...)`; `from_pretrained(...)` plus `index_name` alone is not enough to load a pre-existing index.
- If the model was just indexed or loaded from an index, `index_name` can usually be omitted. If no current index name exists, search prints a warning and returns `None`.
- Passing a different `index_name` updates the model's current index name and reloads the searcher, but it still expects index metadata/collection state to be available on the model.
- `k` is capped internally to the number of passages in the index when it is too large.
- `force_fast=True` configures faster, less exhaustive search settings.
- `zero_index_ranks=True` subtracts 1 from returned ranks, so the best result has rank `0` instead of `1`.
- `doc_ids` filters search by converting document ids through `docid_pid_map` to passage ids. The ids must exist in the loaded index; unknown ids can raise a key lookup error.
- A single string query returns `list[dict]`; a list of queries returns `list[list[dict]]` in query order.

Single-query result schema:

```python
[
    {
        "content": "passage text",
        "score": 42.0,
        "rank": 1,
        "document_id": "source-doc-id",
        "passage_id": 0,
        "document_metadata": {"optional": "metadata"},
    }
]
```

Required keys are `content`, `score`, `rank`, `document_id`, and `passage_id`. `document_metadata` appears only when metadata was indexed for that document id. README examples omit `passage_id`, but the implementation includes it for persisted-index search.

## Add to an Existing Index

Verified signature:

```python
RAG.add_to_index(
    new_collection: list[str],
    new_document_ids = None,
    new_document_metadatas: list[dict] | None = None,
    index_name: str | None = None,
    split_documents: bool = True,
    document_splitter_fn = llama_index_sentence_splitter,
    preprocessing_fn = None,
    bsize: int = 32,
    use_faiss: bool = False,
)
```

Behavior and caveats:

- Support is explicitly experimental and prints a warning.
- `index_name` is required if the model has no current index name.
- New IDs/metadata go through the same consistency checks as `index`.
- Existing document ids are skipped when constructing `new_documents_with_ids`.
- The update path may rebuild the full index when the collection is small or the new batch is large; otherwise it uses ColBERT's `IndexUpdater`.
- Metadata is merged into the existing `docid_metadata_map` when provided.
- Updates persist metadata and collection files back to disk.

## Delete from an Existing Index

Verified signature:

```python
RAG.delete_from_index(
    document_ids,
    index_name: str | None = None,
)
```

Behavior and caveats:

- Support is explicitly experimental and prints a warning.
- `index_name` is required if the model has no current index name.
- Every passage whose `document_id` is in `document_ids` is removed.
- The collection, `pid_docid_map`, and optional `docid_metadata_map` are rewritten after deletion.

## Index Type and FAISS Choice

`ModelIndexFactory.construct("PLAID", ...)` is used by `RAGPretrainedModel.index`; `auto` currently resolves to `PLAID` in the factory. RAGatouille includes placeholders for `FLAT` and `HNSW`, but the persisted index path used here is PLAID.

For smaller collections and `use_faiss=False`, RAGatouille monkey-patches ColBERT k-means to use a PyTorch implementation for compatibility. If that fails, it falls back to FAISS. When CUDA is available but only `faiss-cpu` is installed, indexing prints a warning and continues on CPU after a delay.
