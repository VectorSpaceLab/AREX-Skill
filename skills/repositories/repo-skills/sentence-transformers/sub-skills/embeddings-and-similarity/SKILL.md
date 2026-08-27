---
name: embeddings-and-similarity
description: "Dense SentenceTransformer embedding and similarity workflows for
  text or multimodal inputs, including construction,
  encode/encode_query/encode_document options, prompt and truncation decisions,
  precision, normalization, batching/devices, local cache cautions, and output
  validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Embeddings and Similarity

Use this sub-skill when the user needs dense `SentenceTransformer` embeddings or direct embedding similarity scores.

## Route Here

- Construct or load a `SentenceTransformer` for embedding inference.
- Encode text, images, audio, video, multimodal dicts, or chat-style message inputs with dense embedding models.
- Choose between `encode`, `encode_query`, and `encode_document`, including prompt-aware retrieval embedding.
- Tune `batch_size`, `device`, `precision`, `truncate_dim`, `normalize_embeddings`, output conversion, and similarity metric choices.
- Validate embedding shapes, dtypes, normalization, and similarity matrix or pairwise similarity results.

## Route Elsewhere

- Use `../retrieval-and-utilities/` for `util.semantic_search`, hard-negative mining, paraphrase mining, quantized retrieval indexes, or vector database workflows.
- Use `../evaluation-and-training/` for fine-tuning, losses, trainers, evaluators, and dataset formatting.
- Use `../backend-export-optimization/` for ONNX/OpenVINO backend selection, export, optimization, or deployment packaging.
- Use `../reranking-cross-encoder/` for `CrossEncoder.predict`, `CrossEncoder.rank`, or reranker scoring.
- Use `../sparse-encoder-search/` for `SparseEncoder`, SPLADE-style sparse vectors, sparse search, or sparsity diagnostics.

## Fast Workflow

1. Confirm the task is dense embedding inference, not retrieval orchestration or model training.
2. Load a model with explicit network/cache policy, e.g. `SentenceTransformer(model_id_or_path, local_files_only=True)` for offline use.
3. Prefer `encode_query` and `encode_document` for retrieval models with query/document prompts; use `encode` for symmetric STS, clustering, or classification features.
4. Set output options deliberately: `convert_to_numpy=True` for NumPy workflows, `convert_to_tensor=True` for Torch workflows, and avoid both being ambiguous in reusable code.
5. Validate the returned row count, embedding dimension, dtype, finite values, and similarity output shape before using scores downstream.

## References

- API details: `references/api-reference.md`
- Workflow recipes: `references/workflows.md`
- Failure diagnosis: `references/troubleshooting.md`
- Safe smoke helper: `scripts/dense_embedding_smoke.py`
