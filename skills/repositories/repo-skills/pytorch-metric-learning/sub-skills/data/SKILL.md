---
name: data
description: "Routes PyTorch Metric Learning questions about packaged datasets
  and sampling workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Datasets and sampling

Use this sub-skill when the user wants to download one of the packaged benchmark datasets, define a dataset wrapper, or control batch composition with one of the bundled samplers.

## Typical triggers

- "How do I load CUB, Cars196, iNaturalist2018, or Stanford Online Products?"
- "How do I create a class-balanced batch?"
- "How do I use HierarchicalSampler or FixedSetOfTriplets?"
- "How do I write a custom dataset for this library?"
- "Why does dataset download or split selection fail?"

## In scope

- Datasets: `BaseDataset`, `CUB`, `Cars196`, `INaturalist2018`, `StanfordOnlineProducts`.
- Samplers: `MPerClassSampler`, `HierarchicalSampler`, `TuplesToWeightsSampler`, `FixedSetOfTriplets`.
- Tiny in-memory dataset helpers such as `EmbeddingDataset` when the question is about constructing toy batches or smoke tests.
- Dataset extension patterns from `docs/extend/datasets.md`.

## Out of scope

- Choosing the loss/miner/reducer stack belongs in `components`.
- Trainer hooks, logging, and checkpointing belong in `training`.
- Retrieval metrics and nearest-neighbor search belong in `evaluation`.

## How to use this sub-skill

1. Read `references/datasets-and-samplers.md` for the dataset and sampler map.
2. Run `scripts/smoke_data.py` when you want to confirm a batch-composition rule on toy labels without downloading a benchmark dataset.
3. Read `references/troubleshooting.md` when the failure mentions a missing dataset root, a bad split, or sampler batch-size constraints.
4. If the request is about how a sampler interacts with a trainer, pair this sub-skill with `training` after the sampling choice is clear.

## Common routing decisions

- If the user needs a benchmark dataset and a split name, stay here.
- If the user only needs the retrieval metric after the dataset is loaded, route to `evaluation`.
- If the user only needs the loss that a sampler feeds, route to `components`.

## Useful public facts

- `BaseDataset` defaults to `train+test` and supports `transform`, `target_transform`, and `download`.
- `CUB`, `Cars196`, `INaturalist2018`, and `StanfordOnlineProducts` all provide train/test/train+test style splits.
- `MPerClassSampler` needs enough label structure for the batch size and `m`.
- `HierarchicalSampler` expects hierarchical labels and a true `batch_sampler` slot.
- `TuplesToWeightsSampler` uses a miner and a subset of the dataset to weight the sampling probabilities.
- `FixedSetOfTriplets` is useful when the available supervision is already triplet-shaped.

## Read next

- `references/datasets-and-samplers.md` for the dataset and sampler reference.
- `references/troubleshooting.md` for download and batch-composition failures.
- `scripts/smoke_data.py` for a tiny sampler smoke check.
