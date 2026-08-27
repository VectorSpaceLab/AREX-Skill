# Integrations and Export Workflows

These workflows are designed for future agents using a working RAGatouille installation. They avoid original repository paths and separate lightweight planning from side-effecting model loads, network calls, and uploads.

## 1. LangChain Retriever Over an Existing RAGatouille Index

Use this when the RAGatouille model already has an index and a LangChain chain expects a retriever.

1. Verify imports with `../scripts/check_integration_imports.py`.
2. Load the indexed RAGatouille model with the workflow in `../../pretrained-indexing-search/SKILL.md`.
3. Confirm the index was built with `document_metadatas` if downstream LangChain components need metadata filters, source labels, URLs, or routing keys.
4. Create the retriever with search kwargs captured at construction:

```python
retriever = RAG.as_langchain_retriever(
    index_name="support_docs",
    k=8,
    zero_index_ranks=True,
)
docs = retriever.invoke("How do I rotate an API key?")
```

5. Inspect returned `Document` objects:
   - `page_content` comes from the RAGatouille result `content` field.
   - `metadata` comes from `document_metadata` if indexed, otherwise `{}`.

Metadata routing caveat: adding metadata after indexing will not make it appear in retriever output. Rebuild or update the RAGatouille index with `document_metadatas` first, then wrap it with the LangChain retriever.

## 2. LangChain Compressor for Reranking Candidate Documents

Use this when another retriever provides candidate LangChain `Document` objects and RAGatouille should rescore/rerank them.

```python
compressor = RAG.as_langchain_document_compressor(k=5, bsize="auto")
reranked = compressor.compress_documents(candidate_docs, query="billing escalation")
```

Important behavior:

- The compressor passes each candidate `Document.page_content` into `RAGPretrainedModel.rerank`.
- It returns the original `Document` objects in the reranked order.
- It writes `metadata["relevance_score"]` onto each returned document.
- It does not preserve a separate copy of the original score under another key; rename or copy upstream scores before compression if needed.
- Keep candidate sets modest; route large persistent collections to `../../pretrained-indexing-search/SKILL.md`.

## 3. LlamaIndex or LlamaHub Loaders as Document Sources

Use this when the user wants to ingest content from loader ecosystems rather than local strings.

Legacy example pattern:

```python
from llama_index import download_loader
from ragatouille import RAGPretrainedModel

RAG = RAGPretrainedModel.from_pretrained("colbert-ir/colbertv2.0")
PDFReader = download_loader("PDFReader")
loader = PDFReader()
documents = loader.load_data(file=pdf_path)
texts = [document.text for document in documents]
RAG.index(collection=texts, index_name="pdf_docs", split_documents=True)
```

Modern compatibility checklist:

- Try current LlamaIndex imports first, often under `llama_index.core`, and install loader-specific packages when `download_loader` or `llama_hub` imports fail.
- Confirm each loader document exposes text as `document.text`; if the new object uses another field, normalize it to `list[str]` before calling RAGatouille.
- Treat PubMed, Semantic Scholar, web, arXiv, and many PDF loaders as network, API quota, or file-I/O operations.
- Do not run loader calls in lightweight verification; mock or describe the expected `list[str]` handoff instead.

## 4. Safe Hugging Face Export Handoff

Use this when a trained/local ColBERT checkpoint should be published, but avoid accidental uploads during planning.

Preflight checklist:

1. Confirm the local path is a model checkpoint directory with a readable ColBERT config, not just a persisted RAGatouille document index.
2. Confirm the target Hub repo name in `owner/repo-name` form and whether it should already exist.
3. Confirm `huggingface_hub` login or token handling outside the script, such as `huggingface-cli login` or `HF_TOKEN` in the execution environment.
4. Decide if Vespa ONNX should be included; if yes, run the Vespa preflight below first.
5. Decide if `use_tmp_dir=True` is needed to materialize export files and whether `.tmp/hugging_face_export` is safe to create in the working directory.
6. Only after explicit approval, call:

```python
from ragatouille.models.utils import export_to_huggingface_hub

export_to_huggingface_hub(
    colbert_path="path/to/local-colbert-checkpoint",
    huggingface_repo_name="owner/model-repo",
    export_vespa_onnx=False,
    use_tmp_dir=False,
)
```

Dry-run alternative: use `../scripts/check_integration_imports.py --check-path path/to/local-colbert-checkpoint --repo owner/model-repo --json` to validate imports, path existence, repo-name shape, and credential indicators without loading models or uploading.

## 5. Vespa ONNX Export Planning

Use this when the user needs an ONNX query encoder for a Vespa ColBERT deployment.

Preflight checklist:

1. Confirm `onnx`, `torch`, `transformers`, and RAGatouille export imports succeed.
2. Confirm `out_path` exists and is writable, or create it in an approved workspace.
3. Confirm `colbert_path` is a local checkpoint compatible with `VespaColBERT.from_pretrained`.
4. Check whether `tokenizer.json` exists or whether a fast tokenizer can be saved; missing fast tokenizers may still export but can complicate Vespa packaging.
5. Confirm the user accepts local model loading and ONNX file creation.
6. Only after approval, call:

```python
from ragatouille.models.utils import export_to_vespa_onnx

export_to_vespa_onnx(
    colbert_path="path/to/local-colbert-checkpoint",
    out_path="path/to/export-dir",
    out_file_name="vespa_colbert.onnx",
)
```

## 6. Credential-Bound External LLM Context

Some repository examples show OpenAI/instructor-based synthetic data generation before RAGatouille training. For this sub-skill, treat that material only as evidence of credential-bound external integrations:

- Require `OPENAI_API_KEY` or equivalent service credentials before running external LLM calls.
- Keep generated training data workflows in `../../training-data-finetuning/SKILL.md`.
- Do not bundle notebook cells that hard-code tokens or perform API calls.

## 7. Lightweight CI/Verification Pattern

For a safe check that should not download models, call loaders, or upload:

```bash
python ../scripts/check_integration_imports.py --json
```

Expected successful categories:

- `ragatouille_import`: top-level package imports.
- `langchain_legacy_path`: `BaseDocumentCompressor` legacy import is available.
- `langchain_core`: core `Document` and `BaseRetriever` imports are available.
- `integration_classes`: RAGatouille adapter classes import.
- `export_helpers`: export helper functions import.

Optional warnings for `llama_index`, `huggingface_hub`, or `onnx` should guide installation or runtime planning, not block non-export/non-loader tasks.
