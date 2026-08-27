# Integrations and Export API Reference

This reference captures RAGatouille `0.0.9post2` integration/export surfaces verified from source and installed-package signatures. Use it with `../SKILL.md` for routing and `workflows.md` for recipes.

## LangChain Adapter Methods

### `RAGPretrainedModel.as_langchain_retriever`

Signature:

```python
RAGPretrainedModel.as_langchain_retriever(self, **kwargs: Any) -> langchain_core.retrievers.BaseRetriever
```

Behavior:

- Returns `RAGatouilleLangChainRetriever(model=self, kwargs=kwargs)`.
- The returned retriever calls `self.model.search(query, **kwargs)` from LangChain's `_get_relevant_documents` hook.
- Every RAGatouille search result becomes a LangChain `Document` with:
  - `page_content=doc["content"]`
  - `metadata=doc.get("document_metadata", {})`
- Search kwargs such as `k`, `index_name`, `force_fast`, `zero_index_ranks`, or `doc_ids` can be captured when constructing the retriever.
- Metadata appears only when the underlying RAGatouille index was created with `document_metadatas`; route index setup details to `../../pretrained-indexing-search/SKILL.md`.

Minimal shape:

```python
rag_retriever = RAG.as_langchain_retriever(k=5, index_name="support_docs")
documents = rag_retriever.invoke("How do refunds work?")
```

### `RAGPretrainedModel.as_langchain_document_compressor`

Signature:

```python
RAGPretrainedModel.as_langchain_document_compressor(self, k: int = 5, **kwargs: Any) -> langchain_core.documents.compressor.BaseDocumentCompressor
```

Behavior:

- Returns `RAGatouilleLangChainCompressor(model=self, k=k, kwargs=kwargs)`.
- The compressor consumes an existing sequence of LangChain `Document` objects, extracts each `page_content`, and calls `self.model.rerank(query=query, documents=_docs, k=..., **kwargs)`.
- Output documents are the original `Document` instances in reranked order, with `doc.metadata["relevance_score"] = r["score"]` added or overwritten.
- Runtime `compress_documents(..., k=n)` overrides the constructor `k`; other rerank kwargs are captured at adapter construction.
- Route standalone reranking behavior, result limits, and multi-query caveats to `../../index-free-reranking/SKILL.md`.

Minimal shape:

```python
compressor = RAG.as_langchain_document_compressor(k=3, bsize="auto")
reranked_docs = compressor.compress_documents(candidate_docs, query="renewal policy")
```

## Adapter Classes

### `RAGatouilleLangChainRetriever`

Import:

```python
from ragatouille.integrations import RAGatouilleLangChainRetriever
```

Important fields and methods:

- `model: Any` should be a `RAGPretrainedModel` instance or compatible object with `search(query, **kwargs)`.
- `kwargs: dict = {}` are forwarded to `model.search`.
- `_get_relevant_documents(query, run_manager)` returns `list[langchain_core.documents.Document]`.

Use the factory method unless directly injecting a fake model for tests.

### `RAGatouilleLangChainCompressor`

Import:

```python
from ragatouille.integrations import RAGatouilleLangChainCompressor
```

Important fields and methods:

- `model: Any` should expose `rerank(query, documents, k, **kwargs)`.
- `k: int = 5` controls returned document count unless `compress_documents(..., k=...)` overrides it.
- `kwargs: dict = {}` are forwarded to `model.rerank`.
- `compress_documents(documents, query, callbacks=None, **kwargs)` returns reranked original `Document` objects with `metadata["relevance_score"]`.
- Pydantic config allows arbitrary model types.

## LlamaIndex and LlamaHub Surfaces

RAGatouille has no dedicated LlamaIndex adapter class in this version. The examples use LlamaHub/LlamaIndex loaders as document sources:

1. Import or download a loader, such as `download_loader("PubmedReader")`, `download_loader("PDFReader")`, or `SemanticScholarReader`.
2. Call `loader.load_data(...)` to get loader-specific document objects.
3. Convert each document to text with `document.text`.
4. Pass the resulting `list[str]` to `RAGPretrainedModel.index`.
5. Query with `RAGPretrainedModel.search` or wrap the indexed model as a LangChain retriever.

Compatibility note: older examples import from `llama_index`; newer LlamaIndex releases may require `llama_index.core` for core objects and split loaders into separate packages.

## Export Helpers

### `export_to_huggingface_hub`

Signature:

```python
export_to_huggingface_hub(
    colbert_path: str | pathlib.Path,
    huggingface_repo_name: str,
    export_vespa_onnx: bool = False,
    use_tmp_dir: bool = False,
)
```

Import:

```python
from ragatouille.models.utils import export_to_huggingface_hub
```

Behavior and side effects:

- Loads a ColBERT config with `ColBERTConfig.load_from_checkpoint(colbert_path)`.
- If `use_tmp_dir=True`, loads the ColBERT model from `colbert_path` and saves export files under `.tmp/hugging_face_export`, then removes that temp directory in `finally`.
- If `export_vespa_onnx=True`, checks for a fast tokenizer (`tokenizer.json` or saveable non-legacy tokenizer) and calls `export_to_vespa_onnx` before upload.
- Creates or reuses a Hugging Face model repo with `HfApi().create_repo(..., exist_ok=True)`.
- Uploads the export folder with `HfApi().upload_folder(...)`.
- Catches `ValueError` for login/input errors and `HfHubHTTPError` for missing rights or invalid repo ownership, printing guidance instead of raising in those cases.

Preflight before calling:

- Confirm `colbert_path` is a local model/checkpoint directory, not an index directory unless it contains the required checkpoint config.
- Confirm `huggingface_repo_name` is normally `username/repo-name` and the authenticated user can create or write to it.
- Confirm network access and Hugging Face authentication are approved.
- Decide whether `.tmp/hugging_face_export` can be created or overwritten in the current working directory when `use_tmp_dir=True`.

### `export_to_vespa_onnx`

Signature:

```python
export_to_vespa_onnx(
    colbert_path: str | pathlib.Path,
    out_path: str | pathlib.Path,
    out_file_name: str = "vespa_colbert.onnx",
)
```

Import:

```python
from ragatouille.models.utils import export_to_vespa_onnx
```

Behavior and side effects:

- Instantiates `VespaColBERT.from_pretrained(colbert_path, dim=128)`.
- Exports an ONNX model to `Path(out_path) / out_file_name` using `torch.onnx.export` with opset `17`.
- Uses input names `input_ids`, `attention_mask` and output name `contextual`.
- Declares dynamic axes for batch and sequence dimensions.
- Requires a valid local model checkpoint and the `onnx`/PyTorch export stack.

Preflight before calling:

- Confirm the target checkpoint has a compatible BERT/ColBERT config and weights.
- Confirm `out_path` exists or can be created by the calling workflow; the helper itself converts it to `Path` but does not create parents.
- Confirm `onnx` is installed and the output file can be written.
- Check whether the model has a fast tokenizer when the ONNX export is part of a Vespa deployment package.

## Optional Dependencies and Imports

Declared runtime dependencies include `llama-index`, `langchain`, `langchain_core`, `onnx`, `huggingface_hub` transitively through ColBERT/export code, `torch`, `colbert-ai`, and related retrieval packages.

RAGatouille `0.0.9post2` imports `BaseDocumentCompressor` from `langchain.retrievers.document_compressors.base`; LangChain `1.x` removed that legacy path. A legacy-compatible LangChain set such as `langchain==0.1.20` with matching `langchain_core` was verified during package inspection.
