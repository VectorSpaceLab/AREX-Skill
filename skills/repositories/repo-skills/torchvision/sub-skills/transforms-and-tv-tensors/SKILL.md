---
name: transforms-and-tv-tensors
description: "Build torchvision transforms.v2 pipelines for images, videos,
  masks, boxes, rotated boxes, keypoints, arbitrary samples, migration from v1,
  and TVTensor metadata safety."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# TorchVision Transforms and TVTensors

Use this sub-skill when the task is about `torchvision.transforms.v2`, `torchvision.tv_tensors`, transform migration, dtype/range handling, annotation metadata, custom transforms, functionals, or transform performance.

For dataset construction, downloads, dataset wrapping, image/video IO, or visualization utilities, route to `../datasets-io-utils/`. For model weights preprocessing transforms, route to `../models-and-weights/`. For official training preset scripts, route to `../training-references/`.

## Fast Routing

- Need a v2 pipeline for classification, detection, segmentation, video, keypoints, or nested sample dicts: use `references/pipeline-recipes.md`.
- Need to preserve or repair image, mask, box, rotated-box, video, or keypoint metadata: use `references/tv-tensors-and-annotations.md`.
- Need to migrate a v1 PIL pipeline, write a custom transform, use functionals/kernels, or tune transform speed: use `references/migration-and-performance.md`.
- Need to debug dtype/range, box formats, `canvas_size`, random determinism, PIL/tensor mismatch, TorchScript, or slow transforms: use `references/troubleshooting.md`.
- Need a safe sanity check with no downloads: run `python sub-skills/transforms-and-tv-tensors/scripts/smoke_transform_pipeline.py` from the skill root or copy the script into a project and run it there.

## Default Transform Choices

- Prefer `from torchvision.transforms import v2` for new code; v2 handles images plus boxes, masks, videos, keypoints, and arbitrary nested samples.
- Prefer tensor-first pipelines. Convert PIL inputs with `v2.ToImage()` and use `v2.ToDtype(torch.float32, scale=True)` before `v2.Normalize(...)`.
- Wrap annotation-bearing tensors with `torchvision.tv_tensors` before geometry transforms, especially `BoundingBoxes(..., format=..., canvas_size=(H, W))`, `Mask(...)`, and `KeyPoints(..., canvas_size=(H, W))`.
- Keep labels, ids, file names, and metadata as plain Python values or plain tensors; v2 passes unsupported objects through unchanged.
- Add `v2.SanitizeBoundingBoxes()` or `v2.ClampBoundingBoxes()` after crops/resizes that can remove or partially move boxes.

## Minimal Detection Dict Pattern

```python
import torch
from torchvision import tv_tensors
from torchvision.transforms import v2

image = torch.randint(0, 256, (3, 32, 40), dtype=torch.uint8)
target = {
    "boxes": tv_tensors.BoundingBoxes([[2, 4, 20, 24]], format="XYXY", canvas_size=image.shape[-2:]),
    "labels": torch.tensor([1]),
    "mask": tv_tensors.Mask(torch.zeros((1, 32, 40), dtype=torch.uint8)),
}

transforms = v2.Compose([
    v2.ToImage(),
    v2.RandomHorizontalFlip(p=1.0),
    v2.ToDtype(torch.float32, scale=True),
])
image, target = transforms(image, target)
```

## Safety Checklist

- Check image shape is `(..., C, H, W)` for tensor images and that videos use a supported video layout for the chosen transform.
- Check float images are in `[0, 1]`; uint8 images are in `[0, 255]`.
- Check bounding boxes have the intended `format` and `canvas_size`, and convert with `v2.ConvertBoundingBoxFormat(...)` when needed.
- Check random transforms sample once per call across all fields by using a single v2 transform call on the full sample, not separate calls per field.
- Check scripted code separately: `v2.Compose` is not the TorchScript composition primitive, and scripting v2 classes can fall back to v1-equivalent behavior.
