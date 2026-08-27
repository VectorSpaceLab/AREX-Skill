---
name: training-and-demos
description: "Helps with MinkowskiEngine training pipelines, dataset collation,
  example workflows, reconstruction/completion demos, and multi-GPU recipe
  guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Training and Demos

Use this sub-skill when the task is about data loading, collate functions, example training scripts, reconstruction/completion demos, or multi-GPU recipe guidance.

## What This Route Covers

- `Dataset` / `IterableDataset` patterns for sparse inputs.
- `SparseCollation`, `batch_sparse_collate`, and custom collate functions.
- Quantization-size choice and point-cloud voxelization in training pipelines.
- ModelNet40-style classification recipes, ScanNet-style segmentation recipes, and PointNet variants.
- Reconstruction/completion/VAE demos.
- Multi-GPU, DDP, and Lightning patterns.
- Example-script prerequisites, download caveats, and memory/visualization warnings.

## What It Excludes

- Build/install issues; use `../build-and-install/SKILL.md`.
- Sparse tensor construction details; use `../sparse-tensor-data/SKILL.md`.
- Layer/operator signature details; use `../layers-and-networks/SKILL.md`.

## Read These Bundled Files First

- `references/training-recipes.md` for the main collate and training loop pattern.
- `references/model-and-demo-catalog.md` for the example inventory and skip reasons.
- `references/multigpu.md` for DDP/Lightning guidance.
- `references/data-and-demo-troubleshooting.md` for download/Open3D/memory/display issues.
- `scripts/training_batch_check.py` for a safe synthetic batch and forward-pass smoke.

## Typical Triggers

- You need a sparse DataLoader or collate function.
- You want to adapt one of the repo's example scripts without downloading the full dataset first.
- You need a classification or segmentation recipe around point clouds or voxels.
- You need to understand which examples are reference-only versus safe to run locally.
- You need multi-GPU or Lightning guidance but do not want a full training run.

## Fast Workflow

1. Read the training recipes and the example catalog.
2. Pick the example family that matches the task.
3. Adapt the synthetic smoke or collate pattern before attempting real data.
4. If the task needs dataset downloads, note the prerequisite and keep the default runtime helper safe.
5. For multi-GPU work, read the multi-GPU reference and confirm a CUDA build exists first.

## Public Semantic Rules

- Sparse tensors in a training pipeline should usually be created in the main process when DataLoader workers are involved.
- Quantization size is a model/data hyperparameter and affects the voxel grid directly.
- `torch.cuda.empty_cache()` appears in several repo examples because sparse batch sizes vary.
- Long training, downloads, and visualizations are reference workflows, not default smoke tests.

## Related Helpers

- `../../scripts/check_minkowski_engine.py` — import and tiny package smoke.
- `scripts/training_batch_check.py` — safe synthetic collate and tiny forward-pass check.

## When to Stop

If the issue is really about the sparse tensor API or a layer constructor, route to the sibling sub-skill that owns that topic.
