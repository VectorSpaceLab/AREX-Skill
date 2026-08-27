---
name: sentence-transformers
description: "Use Sentence Transformers for dense embeddings, semantic search,
  CrossEncoder reranking, SparseEncoder search, evaluation/training planning,
  and ONNX/OpenVINO backend optimization. Routes natural language tasks to
  focused sub-skills with bundled references and safe helper scripts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Sentence Transformers

Use this repo skill when a task involves the `sentence-transformers` package for embeddings, retrieval, reranking, sparse search, evaluation, fine-tuning plans, or inference backend optimization.

This root file is a router. Open the matching sub-skill and its linked references before writing code, recommending APIs, or diagnosing failures.

## Install and Verify

Use the smallest public install that matches the task:

```bash
pip install -U sentence-transformers
python - <<'PY'
import sentence_transformers
from sentence_transformers import SentenceTransformer, CrossEncoder, SparseEncoder
print(sentence_transformers.__version__)
print(SentenceTransformer.__name__, CrossEncoder.__name__, SparseEncoder.__name__)
PY
```

Optional extras are task-specific:

- Multimodal inputs: `pip install -U "sentence-transformers[image]"`, `[audio]`, or `[video]`.
- Training: `pip install -U "sentence-transformers[train]"`; add trackers such as `trackio` or `wandb` only when needed.
- ONNX: `pip install -U "sentence-transformers[onnx]"` for CPU or `[onnx-gpu]` for GPU providers.
- OpenVINO: `pip install -U "sentence-transformers[openvino]"`.

## Route by Task

| User request | Open this sub-skill | Why |
| --- | --- | --- |
| Compute dense embeddings, similarity scores, `encode_query`, `encode_document`, prompts, truncation, precision, multimodal inputs | `sub-skills/embeddings-and-similarity/SKILL.md` | Owns `SentenceTransformer` inference and output validation |
| Build semantic search over embeddings, retrieve then rerank, hard-negative mining, quantized embedding search, similarity helpers | `sub-skills/retrieval-and-utilities/SKILL.md` | Owns `sentence_transformers.util` retrieval utilities and orchestration |
| Score text pairs or rerank a candidate list with `CrossEncoder.predict` or `CrossEncoder.rank` | `sub-skills/reranking-cross-encoder/SKILL.md` | Owns reranker APIs, pair/list shapes, and activation/softmax pitfalls |
| Generate sparse embeddings, SPLADE-style search, sparse IR evaluation, sparse service integration | `sub-skills/sparse-encoder-search/SKILL.md` | Owns `SparseEncoder`, sparse vectors, active dims, and sparse-specific troubleshooting |
| Choose losses, evaluators, trainers, dataset shapes, samplers, smoke-test training plans | `sub-skills/evaluation-and-training/SKILL.md` | Owns training/evaluation planning across all three model families |
| Use `backend="onnx"` or `backend="openvino"`, optimize or quantize exported model artifacts | `sub-skills/backend-export-optimization/SKILL.md` | Owns backend extras, provider/file-name options, and export diagnostics |

## Common Decision Points

- Choose `SentenceTransformer` for first-stage retrieval, semantic similarity, clustering, classification via embeddings, and embedding precomputation.
- Choose `CrossEncoder` when scoring `(query, document)` pairs jointly is acceptable and reranking quality matters more than throughput.
- Choose `SparseEncoder` for learned sparse retrieval, lexical expansion, inverted-index-friendly scores, and SPLADE-style workflows.
- Use dense retrieval plus CrossEncoder reranking for high-quality search: retrieve top-k with embeddings, preserve `corpus_id`, then rerank selected texts.
- Keep optional services explicit. FAISS, USearch, Elasticsearch, OpenSearch, Qdrant, Seismic, ONNX Runtime, and OpenVINO require their own extras, packages, or running services.

## Bundled Checks

Run these safe helper scripts from inside this skill directory or pass an explicit script path from any project:

```bash
python sub-skills/retrieval-and-utilities/scripts/semantic_search_demo.py --toy-tensors
python sub-skills/backend-export-optimization/scripts/backend_export_check.py --signatures
python sub-skills/evaluation-and-training/scripts/training_plan_check.py --help
```

Model-loading smoke scripts intentionally require an explicit `--model`; they do not silently download a checkpoint by default.

## Troubleshooting First Reads

- Package install, optional extras, and broad workflow failures: `references/troubleshooting.md`.
- Source freshness and evidence baseline: `references/repo-provenance.md`.
- Workflow-specific failures: open the nearest sub-skill `references/troubleshooting.md`.

## Boundaries

- This skill is for using the public package and its documented APIs, not for maintainer release automation or documentation builds.
- Do not assume large models, Hub downloads, external vector databases, or GPU backends are available unless the user says so or the environment proves it.
- Do not run training, model export, service integration, or native examples as a smoke test unless the user explicitly requests those side effects and prerequisites are present.
