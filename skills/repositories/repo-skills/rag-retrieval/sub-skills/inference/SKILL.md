---
name: inference
description: "Use rag_retrieval Reranker inference APIs to score query-document
  pairs, rerank passages, inspect RankedResults, and debug
  model_type/device/dtype issues."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# rag-retrieval inference

Use this sub-skill when a task asks to use the installed `rag_retrieval` reranker, score query-document pairs, rerank RAG passages, choose a reranker `model_type`, interpret `RankedResults`, or debug inference failures for BGE, BCE, Gemma, MiniCPM, or ColBERT-named rerankers.

## Fast routing

- Start with [API reference](references/api-reference.md) for constructor signatures, model type mappings, return objects, and current limitations.
- Use [workflows](references/workflows.md) for copy-ready scoring, reranking, long-document, LLM prompt, cutoff-layer, and no-download validation patterns.
- Use [troubleshooting](references/troubleshooting.md) when `model_type` is unsupported, ColBERT fails, downloads start unexpectedly, devices/dtypes misbehave, queries are too long, empty docs return a dict, BCE scores look normalized, LLM prompt/cutoff behavior is unclear, or Pydantic warnings appear.

## Scope

This sub-skill covers inference only: `rag_retrieval.Reranker`, cross-encoder rankers, LLM rankers, automatic model-type inference, query-document scoring, document reranking, long-document strategies, normalization, LLM prompt/cutoff-layer behavior, result helpers, and safe no-download environment checks.

Do not use this sub-skill for embedding training, reranker fine-tuning, or ColBERT training. Route those requests to sibling training sub-skills when present. Also do not promise ColBERT inference support: the current package has a `colbert` mapping name, but the ColBERT ranker is not registered or implemented for inference in the installed surface.
