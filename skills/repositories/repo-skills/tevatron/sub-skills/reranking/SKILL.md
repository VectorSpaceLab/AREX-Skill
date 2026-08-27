---
name: reranking
description: "Train and run Tevatron cross-encoder rerankers, prepare pairwise
  rerank inputs, and interpret reranker score outputs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Tevatron Reranking

Use this sub-skill when the task is about Tevatron second-stage cross-encoder reranking: training a reranker from query/positive/negative groups, turning first-stage runs into pairwise JSONL, running reranker inference, using RankLLaMA-style LoRA checkpoints, or interpreting score files.

## Start Here

1. Read [Reranker Workflows](references/reranker-workflows.md) for end-to-end train, inference, rerank-input, and RankLLaMA command plans.
2. Read [Arguments Reference](references/arguments-reference.md) for current `tevatron.reranker.driver.train` and `tevatron.reranker.driver.rerank` arguments, JSONL fields, grouped logits, and LoRA options.
3. Run [prepare_rerank_input.py](scripts/prepare_rerank_input.py) when you have query JSONL, corpus JSONL, and a first-stage run file and need pairwise reranker input.
4. Read [Troubleshooting](references/troubleshooting.md) for pair/triple format mistakes, `train_group_size` mismatches, LoRA adapter issues, missing optional dependencies, score formatting, and download/cache failures.

## Scope Boundaries

This sub-skill covers:

- `tevatron.reranker.driver.train` cross-encoder reranker training.
- `tevatron.reranker.driver.rerank` single-device reranker inference.
- Training JSONL fields, inference JSONL fields, grouped-logit loss behavior, LoRA reranker options, and raw score output interpretation.
- Rerank input preparation from first-stage retrieval runs plus local query/corpus fixtures.
- RankLLaMA-style reranking and training patterns, with cross-links to sibling LLM guidance when the task becomes model-family or hardware specific.

Use sibling Tevatron sub-skills instead for:

- First-stage dense/sparse retriever training: [training](../training/SKILL.md).
- Query/corpus encoding, FAISS search, sharded retrieval, and first-stage ranking files: [encoding-retrieval](../encoding-retrieval/SKILL.md).
- General dataset schema validation and run-format conversion: [data-preparation](../data-preparation/SKILL.md).
- LLaMA/Mistral/Qwen multimodal or LLM retriever hardware/dependency routing beyond reranker-specific flags: [multimodal-llm](../multimodal-llm/SKILL.md).

## Runtime Assumptions

- Tevatron reranker argument dataclasses import in a minimal install, but training and inference require optional `torch` because dataset, collator, model, trainer, and driver modules use PyTorch.
- `transformers` and `datasets` are core Tevatron dependencies; `peft` is required only for `--lora` or `--lora_name_or_path` workflows.
- RankLLaMA/Mistral/LLaMA-style workflows usually require gated model access, GPU memory, compatible precision settings, and optional acceleration packages.
- Keep tiny local JSONL/run fixtures for command validation before launching downloads, GPU jobs, or long training.

## Fast Decision Guide

- Need pairwise rerank JSONL: use [prepare_rerank_input.py](scripts/prepare_rerank_input.py), then verify fields in [Arguments Reference](references/arguments-reference.md#inference-jsonl-fields).
- Need a BERT-style reranker training plan: use [Reranker Workflows](references/reranker-workflows.md#train-a-cross-encoder-reranker).
- Need RankLLaMA or instruction prefixes: use [Reranker Workflows](references/reranker-workflows.md#rankllama-style-reranking-and-training).
- Need to diagnose grouped training loss: use [Troubleshooting](references/troubleshooting.md#train_group_size-and-grouped-logits).
- Need to explain `query_id<TAB>docid<TAB>score`: use [Reranker Workflows](references/reranker-workflows.md#interpret-reranker-output).
