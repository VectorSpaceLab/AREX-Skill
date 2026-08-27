---
name: datasets-io-utils
description: "Use this sub-skill when constructing torchvision datasets,
  validating dataset roots and downloads, wrapping datasets for transforms v2,
  decoding or encoding images with torchvision.io, or using torchvision.utils
  visualization helpers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# TorchVision Datasets, IO, and Utilities

Use this sub-skill for data ingress and small visual checks in TorchVision workflows: built-in datasets, custom `VisionDataset` / `ImageFolder` / `DatasetFolder` code, safe data roots, `wrap_dataset_for_transforms_v2`, image decode/encode APIs, and `torchvision.utils` drawing helpers.

## Route by task

- Dataset construction or root layout: use `references/datasets-and-data-roots.md` for built-in family selection, `ImageFolder`/`DatasetFolder` conventions, `FakeData`, and no-network smoke fixtures.
- Transforms v2 dataset wrapping: start here for `wrap_dataset_for_transforms_v2` dataset support and target-shape expectations, then route transform pipeline internals to `../transforms-and-tv-tensors/`.
- Image IO and visualization: use `references/io-and-visualization.md` for `decode_image`, `read_file`, encoders/writers, `make_grid`, `draw_bounding_boxes`, `draw_segmentation_masks`, `draw_keypoints`, and `flow_to_image`.
- Failures and warnings: use `references/troubleshooting.md` for download races, root layout mistakes, image extension or codec failures, dtype/channel mistakes, video/TorchCodec migration, and visualization label/color errors.
- Model inference or weight preprocessing: route to `../models-and-weights/`; this sub-skill only covers loading/decoding/visualizing data around those workflows.

## Quick safe check

Run the bundled script when an agent needs to verify local TorchVision dataset, image IO, and utility surfaces without network access:

```bash
python sub-skills/datasets-io-utils/scripts/check_dataset_io.py
```

The script creates a temporary two-class `ImageFolder` fixture, uses `FakeData`, attempts `torchvision.io` PNG round-trip if the image extension is available, and exercises `make_grid` plus `draw_bounding_boxes`.

## Hard cases this sub-skill supports

- Build a tiny `ImageFolder` fixture, validate class discovery/order, attach a transform, and verify tensors without downloading real data.
- Diagnose image decode failures by separating path/layout errors, missing image extension support, optional AVIF/HEIC decoder requirements, and PIL fallback options.

## Boundaries

- Do not put augmentation policy details here; link to `../transforms-and-tv-tensors/` for v2 pipelines, TVTensor metadata, bounding-box transform semantics, and dtype/range conversion details.
- Do not cover model output interpretation beyond visualization input requirements; link to `../models-and-weights/` or `../ops-and-detection/` as appropriate.
- Treat legacy C++ IO examples as reference-only gaps; prefer public Python `torchvision.io` and TorchCodec migration guidance.
