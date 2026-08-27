---
name: pretrained-indexing-search
description: "Use RAGatouille RAGPretrainedModel for pretrained checkpoint
  loading, persisted index creation/loading/search, document IDs/metadata, and
  experimental index CRUD."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Pretrained Indexing Search

Use this sub-skill when a task needs RAGatouille's `RAGPretrainedModel` for persisted ColBERT/PLAID indexes: loading a pretrained checkpoint, loading an existing index, building an index from documents, searching it, validating result dictionaries, or doing experimental add/delete updates.

## Route Here For

- Loading models with `RAGPretrainedModel.from_pretrained(...)` or existing persisted indexes with `RAGPretrainedModel.from_index(...)`.
- Creating disk-backed indexes with `RAG.index(...)`, including `document_ids`, `document_metadatas`, splitting, preprocessing, `index_root`, `index_name`, `overwrite_index`, `bsize`, and `use_faiss` choices.
- Searching persisted indexes with `RAG.search(...)`, including single-query vs multi-query result shape, `k`, `doc_ids`, `force_fast`, and `zero_index_ranks`.
- Updating persisted indexes with `RAG.add_to_index(...)` or `RAG.delete_from_index(...)`, while treating CRUD support as experimental.
- Diagnosing input-shape, ID, metadata, index-name, loading, CPU/GPU/FAISS, and dependency compatibility problems before running expensive model work.

## Route Elsewhere

- Use `../index-free-reranking/SKILL.md` for `rerank`, `encode`, `search_encoded_docs`, or small transient in-memory document sets.
- Use `../training-data-finetuning/SKILL.md` for `RAGTrainer`, data prep, hard negatives, training, or fine-tuning.
- Use `../integrations-export/SKILL.md` for LangChain retrievers/compressors, LlamaIndex integration examples, Hugging Face export, or Vespa ONNX export.

## Start Here

1. Read `references/api-reference.md` for verified signatures, defaults, persisted index layout, and result schemas.
2. Read `references/workflows.md` for copyable indexing, existing-index search, metadata, filtering, and CRUD recipes.
3. Read `references/troubleshooting.md` before changing dependencies, running downloads, indexing large corpora, using Windows/WSL, or debugging ID/metadata/search failures.
4. Run `scripts/validate_index_inputs.py --help` when you need an offline sanity check for collection, document ID, and metadata consistency before model downloads or indexing.

## Safety Notes

- `from_pretrained` can download model weights; do not run it in lightweight validation unless downloads are allowed.
- Indexing/search can be slow and may use GPU, FAISS, or PyTorch k-means paths; prefer offline validation and small examples before expensive runs.
- Keep scripts that use RAGatouille inside `if __name__ == "__main__":` when running as standalone programs.
- For RAGatouille 0.0.9post2, avoid latest LangChain 1.x if `import ragatouille` fails on `langchain.retrievers.document_compressors.base`.
