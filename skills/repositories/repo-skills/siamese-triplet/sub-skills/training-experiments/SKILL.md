---
name: training-experiments
description: "Routes shared training-loop, metric, and notebook-experiment tasks
  for the Siamese-triplet repository."
metadata:
  disco-role: operating
disable-model-invocation: true
license: BSD 3-Clause
---

# Training Experiments

Use this sub-skill when the task is about the repository's shared `fit` loop, the sample metrics, the MNIST/FashionMNIST notebooks, or the tiny end-to-end smoke that proves the whole surface still works together.

## Covered surface

- `fit`, `train_epoch`, and `test_epoch`
- `AccumulatedAccuracyMetric`
- `AverageNonzeroTripletsMetric`
- Notebook-style training recipes for MNIST and FashionMNIST
- Embedding extraction and 2D plotting helpers from the notebooks
- Tiny synthetic training passes that avoid dataset downloads

## When to route here

Read this sub-skill for tasks that mention:

- training or validation loops
- optimizer or scheduler wiring
- notebook experiment reconstruction
- embedding visualization
- per-epoch logging
- metric objects for classification or online triplet learning

## What to do first

1. Read `references/workflows.md` for the distilled notebook recipes.
2. Read `references/troubleshooting.md` if a scheduler, metric, or training loop behaves oddly.
3. Run `scripts/tiny_training_smoke.py` when you want a no-download end-to-end check.

## Evidence signals

- Source evidence comes from `trainer.py`, `metrics.py`, README experiment descriptions, and both notebooks.
- The notebooks are expensive examples; the smoke script is the safe executable proxy.
- The fit-loop contract is intentionally broad, so diagnose loader, model, and loss arity together.

## Short workflow

- Match the loader shape to the model and loss shape before calling `fit`.
- Use `AccumulatedAccuracyMetric` for classification setups.
- Use `AverageNonzeroTripletsMetric` when the online triplet loss returns a mined-triplet count.
- For notebook parity, keep the common defaults unless the task explicitly asks for a change:
  - 2D embeddings
  - `margin = 1.0`
  - `Adam`
  - `StepLR(..., step_size=8, gamma=0.1)`

## Decision points

- Choose classification training when you want a baseline embedding plus class head.
- Choose siamese or triplet training when you want pairwise or triplet supervision.
- Choose online mining when batch size and hard-example selection matter more than random pair or triplet sampling.
- Use a synthetic tiny dataset for verification rather than downloading the full torchvision datasets.

## Common failure modes

- The model outputs, loss inputs, and loader batches do not agree on arity.
- Metrics are stateful and must be reset between epochs or smoke passes.
- The repository's notebook code emits a modern PyTorch scheduler-order warning.
- A long notebook run is attempted when only a smoke check was needed.

## Acceptance checks

- A one-epoch classification smoke runs with `ClassificationNet`, `NLLLoss`, and `AccumulatedAccuracyMetric`.
- An online triplet smoke runs with `EmbeddingNet`, `OnlineTripletLoss`, and `AverageNonzeroTripletsMetric`.
- Warnings from modern PyTorch are documented rather than treated as silent failures.
- No smoke check downloads MNIST or FashionMNIST.

## Read next

- `references/workflows.md` for the notebook recipes and distilled defaults.
- `references/troubleshooting.md` for fit-loop and metric issues.
- `../embedding-losses-mining/SKILL.md` if the training issue is actually a loss or selector issue.
- `../dataset-sampling/SKILL.md` if the issue is a loader or sampler issue.
