---
name: reranking-cross-encoder
description: "Use for sentence-transformers CrossEncoder pair scoring,
  reranking, rank API usage, retrieve-and-rerank handoffs, multimodal reranker
  routing, and activation/softmax/num_labels pitfalls."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Reranking Cross Encoder

Use this sub-skill when the task is about scoring input pairs with `CrossEncoder`, reranking an already-retrieved candidate list, choosing between a reranker and a bi-encoder, or debugging CrossEncoder `predict`/`rank` outputs.

## Route Here For

- Pair scoring with `CrossEncoder.predict`, including single pair vs batch-of-pairs shape decisions.
- Reranking an existing list of candidate documents with `CrossEncoder.rank`, `top_k`, `return_documents`, stable `corpus_id` handling, batching, prompts, and device placement.
- Choosing a CrossEncoder reranker over a bi-encoder when accuracy on a limited candidate set matters more than precomputed embeddings or high-throughput first-stage retrieval.
- Regression reranker vs pair-classification setup, especially `num_labels`, `activation_fn`, and `apply_softmax` behavior.
- Multimodal reranker routing for text-image/audio/video-capable CrossEncoder checkpoints.

## Route Elsewhere

- First-stage dense retrieval, `semantic_search`, hard-negative mining, quantized embeddings, and vector database orchestration belong in `../retrieval-and-utilities/SKILL.md`.
- Detailed loss/evaluator/trainer selection belongs in `../evaluation-and-training/SKILL.md`.
- ONNX/OpenVINO export and backend optimization belong in `../backend-export-optimization/SKILL.md`.
- Dense `SentenceTransformer.encode` embeddings and similarity belong in `../embeddings-and-similarity/SKILL.md`.

## Fast Pattern

```python
from sentence_transformers import CrossEncoder

model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L6-v2")
query = "How many people live in Berlin?"
documents = [
    "Berlin had 3,520,031 registered inhabitants.",
    "Berlin is well known for its museums.",
]
results = model.rank(query, documents, top_k=2, return_documents=True)
```

`rank` returns dictionaries sorted by descending score. Each result includes `corpus_id` from the input `documents` list, `score`, and `text` when `return_documents=True`.

## Essential References

- API details: `references/api-reference.md`
- Reranking workflows: `references/workflows.md`
- Failure diagnosis: `references/troubleshooting.md`
- Safe CLI smoke helper: `scripts/cross_encoder_rerank_smoke.py --help`

## Ground Rules

- CrossEncoders score pairs jointly; they do not create reusable document embeddings.
- `rank` is for single-label rerankers (`num_labels == 1`); use `predict` for multi-class pair classifiers.
- Preserve stable corpus IDs by reranking the exact candidate list order and mapping `corpus_id` back to first-stage hits.
- For MS MARCO-style rerankers, raw logits may be unbounded; pass `activation_fn=torch.nn.Sigmoid()` if the downstream consumer needs 0-1 scores. Ranking order is usually unchanged by monotonic activations.
- Do not make the reranker retrieve the whole corpus. Retrieve top candidates first, then rerank only that shortlist.
