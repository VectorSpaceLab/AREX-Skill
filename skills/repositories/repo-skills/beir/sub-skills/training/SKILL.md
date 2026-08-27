---
name: training
description: "Prepare BEIR training pairs and triplets, build evaluators, select
  losses, and plan safe SentenceTransformers training runs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# BEIR Training

Use this sub-skill when the task is to prepare or validate BEIR/SentenceTransformers training inputs, construct `TrainRetriever` data loaders and evaluators, choose BEIR-compatible losses, or plan a safe training invocation.

## Route

- Start with [references/workflows.md](references/workflows.md) for pair/triplet preparation, hard-negative patterns, evaluator setup, and safe training planning.
- Use [references/api-reference.md](references/api-reference.md) for `TrainRetriever`, `BPRLoss`, `MarginMSELoss`, SentenceTransformers loss choices, and fit parameters.
- Use [references/troubleshooting.md](references/troubleshooting.md) for qrels/corpus mismatches, empty dev sets, `max_corpus_size`, triplet shape, dependency compatibility, and expensive training failures.

## Bundled Helper

- Run a no-download training data preflight: `python scripts/training_data_smoke.py`
- Check the `max_corpus_size` guard explicitly: `python scripts/training_data_smoke.py --exercise-max-corpus-error`

The helper imports BEIR training classes, uses tiny in-memory data, validates `InputExample` creation, checks triplet shape expectations, constructs a tiny IR evaluator, and exercises common failure modes without downloading a model or running training.

## Boundaries

- This sub-skill owns `beir.retrieval.train.TrainRetriever`, `beir.losses.BPRLoss`, `beir.losses.MarginMSELoss`, training pair/triplet conversion, evaluator construction for training callbacks, optimizer/scheduler defaults, and training safety planning.
- Route dataset file layout, loader use, and BEIR-format validation to [../data-loading/SKILL.md](../data-loading/SKILL.md).
- Route generated synthetic queries or passage expansion to [../generation/SKILL.md](../generation/SKILL.md).
- Route final retrieval runs and metric reporting after a checkpoint is trained to [../retrieval-evaluation/SKILL.md](../retrieval-evaluation/SKILL.md).
- Route second-stage cross-encoder reranking to [../reranking/SKILL.md](../reranking/SKILL.md).
