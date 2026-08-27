---
name: medical-zoo-pytorch
description: "Operate MedicalZooPytorch 3D medical image segmentation, data
  loading, losses, training, inference, and COVID 2D classification workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# MedicalZooPytorch

Use this repo skill when a task involves MedicalZooPytorch, its `lib.*` modules, 3D medical image segmentation in PyTorch, medical-image dataset loaders, segmentation losses, training/inference loops, or the repository's small 2D COVID classification branch.

## First checks

1. Confirm the MedicalZooPytorch code is available as importable Python modules. This repository exposes `lib.*` directly and may not provide package metadata, so a local checkout often needs its repository root on `PYTHONPATH` or another explicit import path.
2. Install a PyTorch build appropriate for the user's CPU/CUDA environment, then install the non-torch runtime dependencies used by selected workflows: `nibabel`, `scipy`, `matplotlib`, `Pillow`, `tensorboard`, `torchsummary`, `torchsummaryX`, and `torchvision` for the COVID branch.
3. Run the root smoke check before using deeper routes:

```bash
python scripts/smoke_repo_imports.py
python scripts/smoke_repo_imports.py --cuda
```

Use `--package-root /path/to/MedicalZooPytorch` if the modules are not already importable. Do not run full training or the original examples until dataset folders and checkpoint/output paths are confirmed.

## Route by task

- **3D model selection, training, checkpoints, TensorBoard, inference, or visualization:** open [sub-skills/segmentation-workflows/SKILL.md](sub-skills/segmentation-workflows/SKILL.md).
- **Dataset folder layout, loader arguments, image preprocessing, subvolume generation, normalization, resampling, coordinate transforms, or augmentation:** open [sub-skills/data-loading-preprocessing/SKILL.md](sub-skills/data-loading-preprocessing/SKILL.md).
- **Loss selection, Dice/CE/weighted/contrastive/angular losses, one-hot expansion, shape contracts, or trainer criterion return types:** open [sub-skills/losses-and-metrics/SKILL.md](sub-skills/losses-and-metrics/SKILL.md).
- **2D COVID X-ray/CT classification, COVIDx/CovidCT manifests, COVID model caveats, or COVID metric tracking:** open [sub-skills/covid-2d-classification/SKILL.md](sub-skills/covid-2d-classification/SKILL.md).

## Shared references

- [references/workflows.md](references/workflows.md) summarizes the end-to-end route map and how the sub-skills combine.
- [references/troubleshooting.md](references/troubleshooting.md) covers cross-cutting install, data, CUDA, path, and package-import failures.
- [references/repo-provenance.md](references/repo-provenance.md) records the source baseline and evidence paths used to build this skill.
- [references/repo-routing-metadata.json](references/repo-routing-metadata.json) is structured routing metadata for the managed repo-skills router.

## Repository operating model

MedicalZooPytorch is source-tree-oriented rather than packaged like a modern PyPI project. Its public import surface is mostly:

- `lib.medzoo`: model classes plus `create_model(args)`.
- `lib.medloaders`: dataset loader classes plus `generate_datasets(args, path=...)`.
- `lib.losses3D`: factory and concrete loss classes.
- `lib.train`: trainer loops.
- `lib.visual3D_temp`: TensorBoard writer and visualization helpers.
- `lib.utils`: reproducibility, input preparation, checkpoint-era helpers, and COVID metrics.

The old example launchers are valuable evidence, but this skill distills them into bundled references and smoke scripts. Do not point a future user at source examples as required runtime documentation; use the sub-skill workflows instead.

## Backend and data expectations

- CPU is enough for import checks, loss checks, preprocessing checks, and tiny model forward passes.
- CUDA is needed to truthfully exercise paths that move models/tensors with `.cuda()` or that mirror the historical GPU-oriented training/inference examples.
- Real dataset loader runs require the actual ISEG/BraTS/MRBRAINS/IXI/MICCAI/COVID files in the documented folder structure; the repository includes mostly placeholder readmes and some COVID manifest text files, not the full image data.
- Full training and inference are data-heavy and long-running. Use bundled smoke scripts first, then run full experiments only after data paths, output directories, model class, loss return contract, and device placement are confirmed.

## Safe bundled scripts

- `scripts/smoke_repo_imports.py` checks cross-cutting imports and optional CUDA availability.
- Each sub-skill has smaller scripts for its owned workflow. Prefer those before running a complete training job.

## Avoid this skill when

- The task is about another medical-imaging framework such as MONAI, nnU-Net, or TorchIO and does not name MedicalZooPytorch or its APIs.
- The user wants general medical-imaging theory rather than operating this package.
- The task is repository maintenance or code editing rather than package usage; then use normal repo-development context and tests instead of this runtime operating graph.
