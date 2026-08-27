# Troubleshooting: Pretrained Indexing and Search

Use this before running model downloads, large indexing jobs, or experimental CRUD updates.

## Import and Install Failures

### `ModuleNotFoundError: langchain.retrievers.document_compressors.base`

RAGatouille 0.0.9post2 imports LangChain compressor classes at package import time. Latest LangChain 1.x no longer exposes the legacy module path used by this version.

Fix direction:

- Use a legacy-compatible LangChain set for this RAGatouille version.
- Re-run a minimal import check before attempting model downloads:

```python
import ragatouille
from ragatouille import RAGPretrainedModel
```

### `fast_pytorch_kmeans` or `psutil` import/runtime failures

RAGatouille's FAISS-replacement indexing path can rely on `fast-pytorch-kmeans`, which may require `psutil` in the environment. Install/verify `psutil` before debugging ColBERT internals.

### Model download or Hugging Face failures

`RAGPretrainedModel.from_pretrained("colbert-ir/colbertv2.0")` can download checkpoint files. If downloads are blocked or unsafe:

- Use a local checkpoint path if one is already available.
- Use `from_index(index_path)` when a complete persisted index exists.
- Do not treat network failures as input-format failures; validate collection/id/metadata offline first.

## Platform and Runtime Constraints

### Windows and WSL

The project README states Windows is not supported, RAGatouille may work only under WSL, and WSL1 has known issues. Prefer Linux or WSL2 for real indexing/search work.

### Standalone scripts hang or fork unexpectedly

The README says scripts should run RAGatouille code inside:

```python
if __name__ == "__main__":
    main()
```

Use this structure for indexing/search scripts, especially when ColBERT multiprocessing or GPU code might be involved.

## Index Input Validation

### `document_ids must be the same length as collection`

`document_ids` aligns one-to-one with the original `collection`, before document splitting. If one source document splits into many passages, still provide one id for that source document.

### `document_ids must be unique`

Every original document id must be unique. Duplicate ids make metadata and CRUD ambiguous. Use the bundled `scripts/validate_index_inputs.py` to locate duplicates before indexing.

### `document_ids must not contain empty strings`

The implementation calls `.strip()` on ids and rejects empty/whitespace-only ids. In practice, prefer string ids even though the code checks for same-type ids rather than requiring strings. Avoid non-string ids because `.strip()` is string-specific.

### `All document_ids must be of the same type`

Do not mix `"1"` and `1`. Normalize ids to strings before indexing so persisted JSON keys, search filters, and metadata maps are predictable.

### `document_metadatas must be the same length as collection`

Metadata aligns with original source documents, not split passages. Provide one metadata dictionary per original document. Metadata is stored by `document_id` and returned for every passage belonging to that document.

### Metadata missing from results

`document_metadata` appears in search results only if metadata was provided at index creation or added through `add_to_index`. If an index was created without metadata, downstream LangChain/export code cannot recover metadata from the passage text.

## Index Naming and Loading

### Search returns `None` and prints `Cannot search without an index_name`

This happens when the model has no current index name and `search()` was called without `index_name`.

Fix direction:

- Search immediately after `RAG.index(...)`, which sets the current index name and collection state.
- Or load a concrete index directory with `RAGPretrainedModel.from_index(index_path)`.
- Do not expect `RAGPretrainedModel.from_pretrained(...)` plus `search(index_name="...")` to discover and load an existing index by name alone.

### `from_index` cannot load `pid_docid_map.json`

RAGatouille requires `pid_docid_map.json` for current indexes. Older or non-RAGatouille ColBERT indexes may not contain it and can raise an incompatible-index `FileNotFoundError`.

Fix direction:

- Rebuild the index with RAGatouille 0.0.9post2 if possible.
- Verify the path points to the specific index directory, not the parent `indexes/` folder.

### Passing an unexpected `index_name` reloads the searcher

If `search(index_name=...)` differs from the current index name, RAGatouille updates `self.index_name` and reloads the searcher. This is expected but can add latency. Use a stable index name per model instance in latency-sensitive code.

## Search Behavior

### `k` is larger than the index size

RAGatouille prints a warning and lowers `k` to the number of passages in the index. If you filter with `doc_ids`, plan for fewer than `k` hits when the selected documents have fewer passages.

### `doc_ids` filtering fails

`doc_ids` is converted through `docid_pid_map`. Unknown ids can raise key lookup errors. Diagnose by inspecting `pid_docid_map.json` or by validating that the requested ids were used during indexing/addition.

### Ranks start at `0` unexpectedly

`zero_index_ranks=True` subtracts one from the underlying ColBERT rank. Use this when downstream UI/code expects zero-based ranks; otherwise leave it `False` for rank `1` as the top hit.

### Multi-query result handling is wrong

A single string query returns a flat `list[dict]`. A list of query strings returns `list[list[dict]]`. Do not use the same loop for both shapes without normalizing.

### `force_fast=True` changes quality/latency trade-offs

`force_fast=True` uses smaller searcher settings (`ncells`, `ndocs`, threshold). It can reduce latency but may miss results. Avoid it for quality-sensitive comparisons unless the user asked for speed.

## FAISS, GPU, CPU, and Slow Indexing

### PyTorch k-means warning appears

For smaller collections and `use_faiss=False`, RAGatouille prints a warning that it is using an experimental PyTorch replacement for FAISS. This is expected in 0.0.9post2 and improves compatibility for many users.

### PyTorch-based indexing fails and falls back to FAISS

The implementation catches failures in the PyTorch k-means path, prints the error, and retries with FAISS. If both paths fail, check FAISS installation, CPU/GPU compatibility, and collection size.

### GPU exists but only `faiss-cpu` is installed

When CUDA is available but FAISS lacks GPU resources, RAGatouille prints a warning that indexing will be slow and continues with CPU indexing. Install a compatible FAISS GPU build only if the user explicitly wants GPU indexing and the environment supports it.

### Indexing is slow

Expected causes:

- Large collection or long documents.
- `split_documents=True` creating many passages.
- CPU-only PyTorch/FAISS path.
- `use_faiss=False` PyTorch k-means compatibility path.
- Large `k` at search time causing broader searcher settings.

Mitigations:

- Pre-chunk documents and set `split_documents=False`.
- Lower `max_document_length` only when smaller passages make sense.
- Tune `bsize` based on available memory.
- Reuse persisted indexes via `from_index` instead of rebuilding.

## Experimental CRUD

### `add_to_index` warns that support is experimental

This is expected. The method may rebuild the full index for small collections or large additions. It skips new documents whose ids already exist.

Validation after add:

- Check `pid_docid_map.json` contains new ids.
- Check `docid_metadata_map.json` contains new metadata when provided.
- Run a targeted search for the new content.

### `delete_from_index` warns that support is experimental

This is expected. The method removes all passages mapped to the selected document ids and rewrites collection/id/metadata files.

Validation after delete:

- Check deleted ids no longer appear in `pid_docid_map.json`.
- Check deleted ids no longer appear in `docid_metadata_map.json` when metadata exists.
- Run a targeted search and confirm removed content no longer appears.

### CRUD without current `index_name`

Both `add_to_index` and `delete_from_index` need a current index name or an explicit `index_name`. If the model was not loaded from an index and did not just run `index()`, pass `index_name` explicitly.

## Offline Diagnosis Pattern

Before model work, run:

From this sub-skill directory:

```bash
python scripts/validate_index_inputs.py \
  --collection-json '["doc one", "doc two"]' \
  --document-ids-json '["doc-1", "doc-1"]' \
  --document-metadatas-json '[{"source":"a"}]' \
  --json
```

Expected diagnosis includes duplicate document ids and metadata length mismatch. Fix these before calling `RAG.index(...)` or `RAG.add_to_index(...)`.
