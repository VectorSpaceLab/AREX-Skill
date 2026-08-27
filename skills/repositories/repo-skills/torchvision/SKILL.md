---
name: torchvision
description: "Use this skill when working with TorchVision models, weights,
  transforms, TVTensors, datasets, image IO, visualization utilities, vision
  ops, detection helpers, or official reference training workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# TorchVision Repo Skill

Use this skill for practical TorchVision work: choosing models and pretrained weights, building transform pipelines, preparing datasets and image IO checks, using detection/box operators, and planning official reference training commands safely.

TorchVision is a PyTorch computer-vision library. It provides public Python APIs for model architectures, pretrained weight metadata, datasets, transforms, TVTensor metadata types, image IO, visualization helpers, and vision-specific operators.

## Start Here

1. Confirm installation and compatibility with `python scripts/check_torchvision_install.py`.
2. Use `references/package-overview.md` for the module map, supported surfaces, and install/runtime assumptions.
3. Use `references/troubleshooting.md` when imports, compiled ops, downloads, codecs, datasets, or version matching fail.
4. Route to the focused sub-skill below instead of treating this root file as a manual.

## Route by Task

- Model selection, pretrained weights, weight transforms, output interpretation, PyTorch Hub, or feature extraction: use `sub-skills/models-and-weights/`.
- Transform pipelines, v2 migration, TVTensor metadata, boxes/masks/keypoints, random transform behavior, or transform performance: use `sub-skills/transforms-and-tv-tensors/`.
- Built-in/custom datasets, data roots, `ImageFolder`, `FakeData`, image decode/encode, visualization utilities, or no-network fixtures: use `sub-skills/datasets-io-utils/`.
- Box utilities, NMS, ROI Align/Pool, FPN helpers, detection postprocessing, losses/layers, or custom operator errors: use `sub-skills/ops-and-detection/`.
- Official reference training/evaluation scripts, distributed command planning, dataset layout requirements, and safe dry-run training plans: use `sub-skills/training-references/`.

## Minimal Import Check

```bash
python - <<'PY'
import torch
import torchvision
print('torch', torch.__version__)
print('torchvision', torchvision.__version__)
print('ops loaded', torchvision.extension._has_ops())
PY
```

If `ops loaded` is false, pure-Python surfaces may still import, but detection ops such as `torchvision.ops.nms` and many detection models can fail. Use `references/troubleshooting.md` and `sub-skills/ops-and-detection/references/troubleshooting.md`.

## Common Safe Defaults

- Use `weights=None` when tests or examples must avoid network downloads.
- Use weight enums and `weights.transforms()` for real pretrained inference; do not recreate preprocessing by hand unless the task requires it.
- Prefer `torchvision.transforms.v2` for new transform pipelines, especially when samples include boxes, masks, videos, or keypoints.
- Use tiny fixtures, `FakeData`, and bundled smoke scripts before touching real dataset roots or network downloads.
- Treat reference training scripts as command plans by default; they can require datasets, GPUs, distributed launch, and latest-source compatibility.

## Bundled Checks

- `scripts/check_torchvision_install.py`: verifies import, versions, extension availability, important submodules, and no-download smoke surfaces.
- `sub-skills/models-and-weights/scripts/inspect_models.py`: lists models/weights and inspects safe model metadata.
- `sub-skills/transforms-and-tv-tensors/scripts/smoke_transform_pipeline.py`: checks v2 transforms and TVTensor metadata on tiny tensors.
- `sub-skills/datasets-io-utils/scripts/check_dataset_io.py`: creates a tiny no-network dataset/IO fixture.
- `sub-skills/ops-and-detection/scripts/smoke_ops.py`: checks small CPU box/NMS/ROI operator behavior.
- `sub-skills/training-references/scripts/inspect_reference_args.py`: summarizes safe reference-training command families without importing source scripts.

## Evidence and Staleness

Read `references/repo-provenance.md` before trusting this skill for a modified checkout or a new TorchVision release. Refresh the skill if the source commit, public APIs, docs, model catalog, transform semantics, dataset list, compiled ops behavior, or reference scripts changed substantially.
