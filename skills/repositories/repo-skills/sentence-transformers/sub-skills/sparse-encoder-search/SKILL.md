---
name: sparse-encoder-search
description: "Use SparseEncoder for SPLADE-style sparse embeddings, sparse
  similarity/search, sparsity diagnostics, and optional sparse search-service
  integration in sentence-transformers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Sparse Encoder Search

Use this sub-skill when the task is about `SparseEncoder`, SPLADE-style sparse embeddings, lexical expansion, sparse similarity, sparse IR evaluation, sparse losses, or sparse search backends such as Qdrant, Elasticsearch, OpenSearch, or Seismic.

## Route Tasks

- For sparse embeddings, start with `references/api-reference.md` and the safe CLI in `scripts/sparse_encoder_smoke.py`.
- For sparse search, sparsity tuning, hybrid retrieval, and service integration cautions, use `references/workflows.md`.
- For install failures, API shape errors, collapsed sparsity, too many active dimensions, backend/service limits, or training symptoms, use `references/troubleshooting.md`.
- For dense `SentenceTransformer` semantic search utilities, route to `../retrieval-and-utilities/SKILL.md`; use this sub-skill only for sparse embeddings and sparse search adapters.
- For broad fine-tuning plans across dense, cross-encoder, and sparse models, route to `../evaluation-and-training/SKILL.md`; keep this sub-skill focused on sparse-specific losses, evaluators, and diagnostics.
- For ONNX/OpenVINO export and backend optimization, route to `../backend-export-optimization/SKILL.md`.

## Fast Sparse Smoke Check

Run help without loading a model:

```bash
python scripts/sparse_encoder_smoke.py --help
```

Run a local/cached model only when the model files are already available or downloads are allowed:

```bash
python scripts/sparse_encoder_smoke.py --model naver/splade-cocondenser-ensembledistil --sentences "weather today" "sunny outside" --max-active-dims 32
```

Add `--local-files-only` in offline environments.

## Core Decisions

- Use `SparseEncoder.encode_query` and `SparseEncoder.encode_document` for information retrieval when the model has query/document prompts or routes.
- Use `SparseEncoder.encode` for generic sparse embedding and similarity experiments.
- Prefer the default sparse COO tensor output for in-memory sparse similarity; set `convert_to_sparse_tensor=False` only when dense tensors are required by downstream code.
- Use `max_active_dims` to cap non-zero dimensions when memory, latency, or service payload size is too high.
- Check `SparseEncoder.sparsity` before and after tuning or training; sparse models should usually have very high sparsity and a manageable number of active dimensions.
