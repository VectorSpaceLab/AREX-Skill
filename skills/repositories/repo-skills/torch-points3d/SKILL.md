---
name: torch-points3d
description: "Use Torch Points3D for point-cloud deep learning APIs,
  datasets/transforms, Hydra training/evaluation, checkpoints, sparse backend
  decisions, and registration workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Torch Points3D

Use this repo skill when a task involves Torch Points3D, the `torch_points3d`
Python package, point-cloud segmentation/classification/object-detection/
panoptic/registration experiments, Hydra configs under `conf/`, high-level
`PointNet2`/`KPConv`/`RSConv`/`SparseConv3d` APIs, or troubleshooting the old
PyTorch/PyG/sparse-backend stack.

## First Checks

- Read [repo provenance](references/repo-provenance.md) before deciding whether this skill matches a local checkout or should be refreshed.
- Read [installation and compatibility](references/installation-and-compatibility.md) before installing or debugging dependency versions.
- Read [cross-cutting troubleshooting](references/troubleshooting.md) for import failures, CUDA/sparse backend mismatches, Hydra config errors, dataset downloads, W&B/TensorBoard surprises, and checkpoint issues.
- Run [torch_points3d_env_probe.py](scripts/torch_points3d_env_probe.py) for a safe import/version/backend diagnostic.

## Minimal Install Pattern

Torch Points3D is a legacy PyTorch/PyG stack. Install a compatible PyTorch build
first, then the matching PyG extension wheels, then Torch Points3D and optional
workflow packages:

```bash
python -m pip install "torch==1.8.*" "torchvision==0.9.*"
python -m pip install "torch-geometric==1.7.*" "torch-scatter==2.0.*" \
  "torch-sparse>=0.6.10,<0.6.13" "torch-cluster==1.5.*"
python -m pip install torch-points3d
python - <<'PY'
import torch, torch_points3d
print(torch.__version__)
print(torch_points3d.__name__)
PY
```

For modern CUDA, old wheels may not exist. Prefer a version-matched legacy
Python environment for reproduction, or build the compiled extensions from
source. Do not claim sparse models are runnable until `MinkowskiEngine` or
`torchsparse` imports in the target environment.

## Route by Task

- Use [model-apis](sub-skills/model-apis/SKILL.md) for high-level application constructors (`PointNet2`, `KPConv`, `RSConv`, `SparseConv3d`), standalone forward smokes, pretrained registry tags, and dense/partial-dense/sparse backend choices.
- Use [datasets-transforms](sub-skills/datasets-transforms/SKILL.md) for dataset config resolution, Torch Geometric `Data`/`Batch` expectations, transform/filter YAML, collate rules, ScanNet/S3DIS/ShapeNet/ModelNet/SemanticKITTI layouts, and safe dataset preflight checks.
- Use [training-evaluation](sub-skills/training-evaluation/SKILL.md) for Hydra `train.py`/`eval.py` workflows, `Trainer`, checkpoint resume/eval, visualization/logging, experiment output discovery, and forward inference from checkpoints.
- Use [registration-workflows](sub-skills/registration-workflows/SKILL.md) for 3DMatch/KITTI/ETH/TUM/KAIST/ModelNet registration configs, pair/fragment data contracts, descriptor evaluation, FPS sampling, and registration-specific backend caveats.

## Shared Decision Rules

- Start with a CPU import/config smoke before any training, dataset download, checkpoint download, or GPU/sparse backend build.
- Treat `conf/` as the source of command composition. Training commands need `task`, `models`, `data`, and `model_name` overrides that resolve together.
- Dense PointNet2/RSConv examples use batched tensors shaped like `[B, N, C]` for features and `[B, N, 3]` for positions; KPConv and sparse workflows use PyG-style variable-size `Data` batches.
- `SparseConv3d`, `Minkowski` models, PointGroup, PVCNN/MS-SVConv, and some registration paths require optional sparse backends. Missing optional backend imports are not package-wide failures; route to the relevant troubleshooting page.
- Disable or explicitly configure W&B/TensorBoard/profiling for short local smoke runs unless the user wants logging artifacts.
- Dataset acquisition can involve external licenses, large downloads, or credentials. Prefer tiny fixtures, config composition, and layout validation before launching downloads.

## Safe Shared Command

```bash
python scripts/torch_points3d_env_probe.py --json
```

Use `--require-package`, `--require-pyg`, or `--require-sparse-backend` when a
task needs a hard pass/fail diagnostic instead of an informational report.
