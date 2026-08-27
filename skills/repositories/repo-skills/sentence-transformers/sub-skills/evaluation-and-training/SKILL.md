---
name: evaluation-and-training
description: "Route sentence-transformers evaluation and training tasks across
  SentenceTransformer, CrossEncoder, and SparseEncoder trainers, losses,
  evaluators, dataset shapes, samplers, smoke tests, and safe training
  scaffolding."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Evaluation and Training

Use this sub-skill when a task asks how to evaluate, fine-tune, smoke-test, or debug training for `SentenceTransformer`, `CrossEncoder`, or `SparseEncoder` models.

Keep this file as the router. Open the references before writing code or giving final training advice.

## Route by request

| Request | Read first | Use for |
| --- | --- | --- |
| Build a safe training workflow | `references/training-reference.md` | Trainer classes, training args, datasets, samplers, model cards, baseline eval, smoke tests |
| Pick evaluator or `metric_for_best_model` | `references/evaluation-reference.md` | Evaluator families, primary metric keys, baseline/final eval practice |
| Match data shape to loss | `references/loss-routing.md` | Dense, reranker, sparse, distillation, pair/list/triplet routing |
| Diagnose failures | `references/troubleshooting.md` | Install extras, API misuse, metrics, samplers, optional backends/services |
| Validate a proposed plan without training | `scripts/training_plan_check.py` | Static checks for model type, data shape, loss, evaluator, sampler, and extras |

## Model-type routing

- Use `SentenceTransformerTrainer` for dense bi-encoders: retrieval embeddings, STS, clustering, paraphrase mining, distillation, Matryoshka, static embeddings, and most vector-search fine-tuning.
- Use `CrossEncoderTrainer` for rerankers or pair classifiers: pair scoring, top-K reranking, NLI-style classification, BCE/ranking/listwise reranker losses.
- Use `SparseEncoderTrainer` for SPLADE-style learned sparse retrieval: sparse vectors, inverted-index retrieval, FLOPS regularization, sparse/distillation losses.
- If the task is really about choosing model architecture, prompts, multimodal support, reranking inference, sparse search, or backend export, route to the relevant model or backend sub-skill first, then return here for evaluation/training details.

## Non-negotiable training checks

- Install the training stack before training: `pip install "sentence-transformers[train]"`; add `image`, `audio`, or `video` extras only for multimodal data.
- Use `datasets.Dataset` or `DatasetDict`; label columns must be named `label`, `labels`, `score`, or `scores`; other columns are inputs and their order matters.
- Run the evaluator once before `trainer.train()` to record a baseline, then compare final or best-checkpoint metrics against it.
- For contrastive dense/sparse losses, set `batch_sampler=BatchSamplers.NO_DUPLICATES`; for batch triplet losses, use `BatchSamplers.GROUP_BY_LABEL`.
- For multi-dataset training, set `multi_dataset_batch_sampler=MultiDatasetBatchSamplers.PROPORTIONAL` or `ROUND_ROBIN` deliberately.
- Smoke-test every long run with a tiny dataset slice and `max_steps=1` before committing GPU time.

## Script quick check

Run the bundled checker to catch common plan mismatches before writing a full script:

```bash
python sub-skills/evaluation-and-training/scripts/training_plan_check.py \
  --model-type cross-encoder \
  --data-shape pair-binary \
  --loss BinaryCrossEntropyLoss \
  --evaluator CrossEncoderRerankingEvaluator
```

The checker is static and does not import or train `sentence-transformers`; it validates routing assumptions and prints warnings to carry into the real script.
