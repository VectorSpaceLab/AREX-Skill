---
name: embedding-losses-mining
description: "Routes embedding-network, contrastive-loss, triplet-loss, and
  online mining tasks for the Siamese-triplet repository."
metadata:
  disco-role: operating
disable-model-invocation: true
license: BSD 3-Clause
---

# Embedding, Losses, and Mining

Use this sub-skill when the task is about the repository's embedding backbone, the siamese and triplet wrappers, the contrastive or triplet losses, or the pair/triplet selection helpers used for online mining.

## Covered surface

- `EmbeddingNet`
- `EmbeddingNetL2`
- `ClassificationNet`
- `SiameseNet`
- `TripletNet`
- `ContrastiveLoss`
- `TripletLoss`
- `OnlineContrastiveLoss`
- `OnlineTripletLoss`
- `PairSelector` and `TripletSelector` implementations

## When to route here

Read this sub-skill for tasks that mention:

- image embeddings
- Siamese or triplet networks
- contrastive or triplet margin losses
- hard negative mining
- pair or triplet selectors
- online contrastive or online triplet learning
- 2D embedding backbones and post-backbone classification heads

## What to do first

1. Read `references/api-reference.md` for shapes and return values.
2. Read `references/troubleshooting.md` if a selector or loss returns empty results.
3. Run `scripts/check_losses_networks.py` for a tiny no-download smoke.

## Evidence signals

- Source evidence comes from `networks.py`, `losses.py`, `utils.py`, README loss descriptions, and the notebook training cells.
- The surface is pure PyTorch; CPU verification covers the selected behavior, while CUDA is an optional acceleration path.
- The smoke script checks object construction, tensor shapes, selector outputs, and online-loss return contracts.

## Short workflow

- Instantiate `EmbeddingNet` and verify that it maps `1×28×28` images to a 2D embedding.
- Wrap the backbone with `ClassificationNet`, `SiameseNet`, or `TripletNet` depending on the downstream loss.
- Choose the loss:
  - `ContrastiveLoss` for pairwise same/different supervision
  - `TripletLoss` for explicit anchor/positive/negative supervision
  - `OnlineContrastiveLoss` or `OnlineTripletLoss` when mining pairs or triplets inside a mini-batch
- For online mining, pair the loss with a selector that matches the batch structure and label density.

## Decision points

- Use `EmbeddingNetL2` if normalized embeddings are important.
- Use `ClassificationNet` only when the task is ordinary classification rather than metric learning.
- Use `HardNegativePairSelector` when you want the hardest negative pairs from a batch.
- Use one of the triplet selector factories when you want exhaustive, random hard, or semi-hard negative mining.
- Keep the margin the same between the loss and the selector strategy unless the reference explicitly says otherwise.

## Common failure modes

- The selector sees too few examples per class and cannot mine meaningful pairs or triplets.
- The code assumes CPU-friendly selector logic, so large batches can become expensive even when the backbone is on GPU.
- `OnlineTripletLoss` returns `(loss, num_triplets)`, which is easy to misuse if a caller expects a plain tensor.
- `EmbeddingNetL2` divides by the norm without an epsilon guard.

## Acceptance checks

- Network wrappers produce outputs with the expected arity.
- Direct losses return scalar tensors.
- Online contrastive loss returns a scalar tensor.
- Online triplet loss returns a scalar tensor plus a mined-triplet count.
- Selector fixtures contain at least two samples per class.

## Read next

- `references/api-reference.md` for the module and selector map.
- `references/troubleshooting.md` for CPU/GPU and empty-mining issues.
- `../dataset-sampling/SKILL.md` if the next step is a wrapper or sampler problem.
- `../training-experiments/SKILL.md` if the next step is a fit-loop or notebook workflow check.
