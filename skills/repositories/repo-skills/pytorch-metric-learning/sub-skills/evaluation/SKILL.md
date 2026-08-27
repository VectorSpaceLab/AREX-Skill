---
name: evaluation
description: "Routes PyTorch Metric Learning questions about AccuracyCalculator,
  testers, and nearest-neighbor inference."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Evaluation and inference

Use this sub-skill when the user wants to score an embedding space, compare query/reference splits, or perform nearest-neighbor lookup after training.

## Typical triggers

- "How do I compute precision@1, mAP, R-precision, NMI, or AMI?"
- "How do I use GlobalEmbeddingSpaceTester or the other testers?"
- "How do I do nearest-neighbor search on embeddings?"
- "How do I save or reload the faiss index?"
- "How do I compare query and reference splits or use a custom label-comparison function?"

## In scope

- Accuracy: `AccuracyCalculator` and its metric family (`precision_at_1`, `r_precision`, `mean_average_precision`, `mean_average_precision_at_r`, `mean_reciprocal_rank`, `NMI`, `AMI`).
- Testers: `GlobalEmbeddingSpaceTester`, `WithSameParentLabelTester`, `GlobalTwoStreamEmbeddingSpaceTester`, and `BaseTester`.
- Inference: `InferenceModel`, `MatchFinder`, `FaissKNN`, `FaissKMeans`, `CustomKNN`.
- Tiny in-memory datasets for evaluation smoke checks, including `EmbeddingDataset`.

## Out of scope

- Choosing the loss/miner stack belongs in `components`.
- Training loop, logging, and checkpointing belong in `training`.
- Dataset download and sampler construction belong in `data` unless the question is purely about evaluation input shape.

## How to use this sub-skill

1. Read `references/evaluation-and-inference.md` for the metric map, tester usage, and inference search patterns.
2. Run `scripts/smoke_evaluation.py` when you want a tiny confirmation that `AccuracyCalculator`, a tester, and `InferenceModel` still work together.
3. Read `references/troubleshooting.md` when the failure mentions faiss, `k`, custom label comparison, or an untrained index.
4. If the user is still deciding which loss/miner stack to train, route to `components` before finalizing the evaluation settings.

## Common routing decisions

- If the user only needs a metric definition or retrieval score, stay here.
- If the user asks how to choose a validation hook or checkpoint policy, route to `training`.
- If the user asks for the right dataset split or sampler input before evaluation, route to `data`.

## Useful public facts

- `AccuracyCalculator` can include or exclude metrics, and `k` can be `None`, a positive integer, or `"max_bin_count"`.
- `ref_includes_query=True` is the right choice when the query set is part of the reference set.
- `GlobalEmbeddingSpaceTester` is the usual default tester for embedding retrieval tasks.
- `WithSameParentLabelTester` expects hierarchical labels.
- `GlobalTwoStreamEmbeddingSpaceTester` expects datasets that yield `(anchor, positive, label)`.
- `InferenceModel` defaults to a faiss-backed k-NN index if you do not override `knn_func`.

## Read next

- `references/evaluation-and-inference.md` for the metric, tester, and inference reference.
- `references/troubleshooting.md` for faiss, `k`, and label-comparison failures.
- `scripts/smoke_evaluation.py` for a tiny evaluation and inference smoke check.
