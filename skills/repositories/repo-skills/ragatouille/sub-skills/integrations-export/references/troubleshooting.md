# Integrations and Export Troubleshooting

Use this guide when integration imports, framework adapters, external loaders, or export helpers fail.

## `import ragatouille` Fails on LangChain 1.x

Symptom examples:

- `ModuleNotFoundError: No module named 'langchain.retrievers.document_compressors.base'`
- Importing `RAGPretrainedModel` fails before any model code runs.

Cause:

- RAGatouille `0.0.9post2` imports `BaseDocumentCompressor` from the legacy `langchain.retrievers.document_compressors.base` path. Latest LangChain `1.x` no longer exposes that module.

Fix:

- Use a legacy-compatible LangChain set for this RAGatouille version, such as `langchain==0.1.20` with a compatible `langchain_core` release.
- Run `../scripts/check_integration_imports.py --json` to confirm the legacy path and adapter imports before model work.
- Avoid upgrading only `langchain_core` or only `langchain`; mismatched LangChain package versions can move classes or break pydantic model behavior.

## `fast_pytorch_kmeans` or `psutil` Import Failures

Symptom examples:

- `ModuleNotFoundError: No module named 'psutil'`
- Import chains fail while importing RAGatouille dependencies before integration code runs.

Fix:

- Install `psutil` in the same environment as RAGatouille when the fast-kmeans dependency chain requires it.
- Re-run the import checker before debugging LangChain or export code.

## LangChain Retriever Returns Empty Metadata

Likely causes:

- The RAGatouille index was built without `document_metadatas`.
- Metadata length did not match the collection during indexing, so indexing failed or used a different collection.
- The task is using the compressor, which preserves and mutates candidate `Document.metadata`, not index metadata.

Fix:

- Rebuild or update the index with `document_metadatas` using `../../pretrained-indexing-search/SKILL.md`.
- Confirm search results contain `document_metadata` before wrapping as a LangChain retriever.
- For compressor pipelines, preserve upstream metadata before reranking and read `metadata["relevance_score"]` after compression.

## LangChain Compressor Mutates Documents

Symptom:

- Candidate `Document` metadata now contains or overwrites `relevance_score`.

Cause:

- `RAGatouilleLangChainCompressor.compress_documents` appends scores to the original document objects returned in reranked order.

Fix:

- Copy candidate documents before compression if upstream metadata must remain immutable.
- Rename existing scores before compression if a previous retriever already uses `relevance_score`.

## LlamaIndex Import Path Changes

Symptom examples:

- `ImportError` for `from llama_index import Document` or `SentenceSplitter`.
- `download_loader` is missing.
- `llama_hub` modules cannot be imported.

Cause:

- LlamaIndex reorganized core imports and loaders across releases. Older examples use `llama_index` and `llama_hub`; newer environments may require `llama_index.core` and separate loader packages.

Fix:

- Try current imports from `llama_index.core` for core objects.
- Install the specific loader integration package required by the loader, rather than assuming `llama-index` includes all loaders.
- Normalize loader outputs to `list[str]` through `document.text` or the new text field before passing them into RAGatouille.
- Treat `download_loader` as potentially network-bound and unsuitable for lightweight verification.

## External Loader, Network, or API-Key Failures

Symptom examples:

- PubMed, Semantic Scholar, arXiv, PDF, or web loader calls fail.
- OpenAI/instructor examples fail with missing `OPENAI_API_KEY`.
- Loader calls hang or hit rate limits.

Fix:

- Separate loader verification from RAGatouille verification: first prove the loader returns document-like objects, then pass a small `list[str]` into RAGatouille.
- Ask for explicit approval before network/API calls in constrained environments.
- Keep credentials in environment variables or service login state; never hard-code tokens.
- Cache or fixture loader output for tests when possible.

## Hugging Face Export Auth or Permission Errors

Symptom examples:

- The helper prints that it could not create a repository and suggests `huggingface-cli login`.
- The helper prints that the user lacks rights to create the repository name.
- Upload silently does not appear where expected.

Likely causes:

- No Hugging Face token/login is available.
- Repo name is not in `owner/repo-name` form.
- The authenticated user does not own `owner` or lacks write permission.
- Network access is blocked.

Fix:

- Validate repo-name shape with the bundled checker: `../scripts/check_integration_imports.py --repo owner/model-repo --json`.
- Confirm `huggingface-cli whoami` or equivalent token-based auth outside runtime skill content.
- Confirm upload approval before calling `export_to_huggingface_hub`; it performs network writes.
- Use a private dry-run plan for path/auth/config checks, then run the upload only in the approved deployment environment.

## Invalid ColBERT Export Path

Symptom examples:

- `ColBERTConfig.load_from_checkpoint` cannot load a config.
- `VespaColBERT.from_pretrained` cannot instantiate the model.
- Export code prints that the path does not contain a valid ColBERT config.

Fix:

- Confirm the path points to a trained/local ColBERT checkpoint, not only a RAGatouille document index or an arbitrary directory.
- If the model was trained through `RAGTrainer.train`, use the returned checkpoint path.
- If the path came from an index, identify the associated checkpoint before exporting.

## Vespa ONNX Export Fails

Symptom examples:

- `ModuleNotFoundError: No module named 'onnx'`.
- `torch.onnx.export` errors.
- Output path errors for `vespa_colbert.onnx`.
- Warning that the tokenizer has no fast tokenizer implementation.

Fix:

- Install and verify `onnx`, `torch`, and compatible `transformers` in the execution environment.
- Ensure `out_path` exists and is writable before calling `export_to_vespa_onnx`.
- Confirm the model is BERT/ColBERT-compatible and uses the expected `dim=128` projection.
- For Vespa packaging, prefer checkpoints with `tokenizer.json` or a tokenizer that can save in non-legacy fast-tokenizer format.
- Treat missing fast-tokenizer warnings as deployment caveats even when ONNX export completes.

## `.tmp/hugging_face_export` Cleanup Problems

Cause:

- `export_to_huggingface_hub(..., use_tmp_dir=True)` writes `.tmp/hugging_face_export` and removes it in `finally`.

Fix:

- Run from a working directory where `.tmp/` can be created and deleted.
- Avoid concurrent exports from the same working directory.
- If preserving export artifacts matters, export to a dedicated directory with lower-level helper calls rather than relying on the temp path.
