---
name: embeddings-retrieval
description: "Use UniLM E5 and SimLM for embedding evaluation, dense retrieval,
  reranking, hard-negative mining, teacher scoring, and retrieval training
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Embeddings Retrieval

Use this sub-skill when a task names E5, SimLM, BEIR, MTEB, MS MARCO, DPR/NQ retrieval, dense corpus/query encoding, reranking, hard-negative mining, or teacher-score generation.

For general sequence-to-sequence generation, route to `language-seq2seq`. For image-text or document AI retrieval that does not explicitly name E5 or SimLM, route to `vision-document-ai`. For PFPO/ReSA math evaluation or generic training architecture questions, route to `architectures-training`.

## Fast Routing

- Choose **E5** for off-the-shelf text embeddings, BEIR retrieval evaluation, non-retrieval MTEB tasks, multilingual embeddings, and prefix/pooling questions.
- Choose **SimLM biencoder** for dense passage retrieval pipelines that separately encode a corpus, encode/search queries, and optionally mine hard negatives from search output.
- Choose **SimLM reranker** for cross-encoder scoring of `(query, candidate passage)` pairs from an existing top-k run; do not use it to encode a corpus.
- Choose **SimLM RLM/KD training** for replacing-language-model pretraining, distillation data generation, or retraining MS MARCO/DPR retrieval models.

## Bundled References and Script

- Read `references/model-and-data-reference.md` to choose E5/SimLM model families, prefixes, pooling, dependencies, file roles, and data layouts.
- Read `references/workflows.md` to construct safe E5 evaluation commands and plan SimLM encode/search/rerank/train/teacher-score phases.
- Read `references/troubleshooting.md` when prefixes, multilingual flags, GPU memory, downloads, DeepSpeed, or missing SimLM data files break a workflow.
- Run `scripts/build_e5_eval_command.py --help` to print a validated E5 BEIR or MTEB command without downloading data, loading a model, or launching evaluation.

## Safety Defaults

- Treat E5 BEIR/MTEB evaluation as network- and GPU-heavy: the upstream scripts download benchmark data/model weights and can run for hours.
- Treat SimLM download, train, encode, search, rerank, and teacher-score scripts as reference-only unless the user has explicitly provided data, GPUs, storage, and permission for long jobs.
- Prefer command construction, file validation, and dry-run planning before any native run. SimLM code asserts CUDA availability for core training/inference paths.
- Keep generated commands rooted in a caller-provided working copy or environment; this skill does not require or expose the original source checkout.
