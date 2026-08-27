---
name: minkowski-engine
description: "Helps with MinkowskiEngine install/build troubleshooting, sparse
  tensor workflows, sparse convolution and network construction, and the repo's
  training and demo patterns."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# MinkowskiEngine

Use this skill for the NVIDIA MinkowskiEngine repository when the task involves sparse tensors, sparse convolutions, point-cloud or voxel workflows, or package installation and build troubleshooting.

## Start Here

- If the package is not installed, build fails, or CUDA/BLAS/compiler setup is unclear, read `sub-skills/build-and-install/SKILL.md` first.
- If the task is about `SparseTensor`, `TensorField`, quantization, batching, coordinate managers, or dense/sparse conversion, use `sub-skills/sparse-tensor-data/SKILL.md`.
- If the task is about convolution, pooling, normalization, pruning, interpolation, union, kernel generators, or custom sparse networks, use `sub-skills/layers-and-networks/SKILL.md`.
- If the task is about training pipelines, ModelNet40, ScanNet-style demos, PointNet variants, reconstruction/completion, or multi-GPU patterns, use `sub-skills/training-and-demos/SKILL.md`.

## Minimum Install and Smoke Check

Basic public install routes are:

```bash
python -m pip install -U torch numpy ninja
python -m pip install -U MinkowskiEngine
```

For custom CPU/CUDA/BLAS source builds, use `sub-skills/build-and-install/SKILL.md` instead of guessing flags.

After installation, run the bundled smoke helper from this skill directory or resolve the same bundled script path from the skill tree:

```bash
python scripts/check_minkowski_engine.py --help
python scripts/check_minkowski_engine.py --smoke
```

Use `--repo-root` only when you intentionally want the helper to inspect a local checkout instead of the installed package.

## What This Skill Covers

- Source builds and install diagnosis for CPU-only and CUDA variants.
- Sparse tensor creation, quantization, batching, coordinate reuse, and dense/sparse conversion.
- Sparse convolutional and pooling layers, broadcast, normalization, pruning, interpolation, union, and simple network construction.
- Training/demo recipes for sparse point clouds and voxelized data.

## Read These Bundled References

- `references/repo-provenance.md` when checking whether this skill matches the current repository revision or before refreshing it.
- `references/troubleshooting.md` for cross-cutting install, import, and runtime failures.
- `sub-skills/build-and-install/references/build-reference.md` for build flags, compiler variables, and source install choices.
- `sub-skills/sparse-tensor-data/references/api-reference.md` and `sub-skills/sparse-tensor-data/references/workflows.md` for coordinate, quantization, and sparse tensor usage.
- `sub-skills/layers-and-networks/references/api-reference.md` and `sub-skills/layers-and-networks/references/workflows.md` for layer and model construction.
- `sub-skills/training-and-demos/references/training-recipes.md` for collate, quantization, and demo/training patterns.

## Fast Routing Rules

- Build or import error, missing backend, compiler/toolkit mismatch, BLAS selection, or Docker build: go to `build-and-install`.
- Coordinates, voxelization, `SparseTensor` shape or key errors, `TensorField`, or dense conversion: go to `sparse-tensor-data`.
- Convolution, pooling, nonlinearities, residual blocks, pruning, interpolation, or network skeletons: go to `layers-and-networks`.
- Dataset collation, training loop structure, example scripts, reconstruction/completion, or multi-GPU demos: go to `training-and-demos`.

## Notes

- This generated skill is self-contained; it should not rely on the original checkout remaining available.
- When you need precise public provenance or staleness checks, read `references/repo-provenance.md`.
- Optional CUDA behavior exists in the repo, but the drafted inspection environment verified only the CPU build. Treat GPU guidance as optional unless you have a verified CUDA build for the current checkout.
