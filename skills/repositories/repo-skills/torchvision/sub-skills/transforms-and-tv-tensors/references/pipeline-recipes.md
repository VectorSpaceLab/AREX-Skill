# Pipeline Recipes

Use `torchvision.transforms.v2` for new transform code. The core advantage is that one transform call can update every supported object in a sample consistently: image, video, bounding boxes, rotated bounding boxes, masks, keypoints, labels that need sanitization, and arbitrary nested structures.

## Classification Tensor Pipeline

```python
import torch
from torchvision.transforms import v2

transforms = v2.Compose([
    v2.ToImage(),
    v2.ToDtype(torch.uint8, scale=True),
    v2.RandomResizedCrop((224, 224), antialias=True),
    v2.RandomHorizontalFlip(p=0.5),
    v2.ToDtype(torch.float32, scale=True),
    v2.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])
```

Notes:
- `v2.ToImage()` converts PIL images or compatible tensors into image-like tensor inputs.
- `v2.ToDtype(torch.float32, scale=True)` maps integer image ranges such as `[0, 255]` to float `[0, 1]`.
- `Normalize` expects float tensors, usually after scaling.
- For model-specific weight preprocessing, prefer the weight enum transforms and route to `../../models-and-weights/`.

## Detection Sample Dict

```python
import torch
from torchvision import tv_tensors
from torchvision.transforms import v2

height, width = 64, 80
sample = {
    "image": tv_tensors.Image(torch.randint(0, 256, (3, height, width), dtype=torch.uint8)),
    "target": {
        "boxes": tv_tensors.BoundingBoxes(
            [[5, 6, 40, 45], [20, 15, 70, 55]],
            format="XYXY",
            canvas_size=(height, width),
        ),
        "labels": torch.tensor([3, 7]),
        "masks": tv_tensors.Mask(torch.zeros((2, height, width), dtype=torch.uint8)),
        "image_id": "debug-sample-0001",
    },
}

def labels_getter(sample):
    return sample["target"]["labels"]

transforms = v2.Compose([
    v2.RandomHorizontalFlip(p=0.5),
    v2.RandomIoUCrop(),
    v2.SanitizeBoundingBoxes(labels_getter=labels_getter),
    v2.ToDtype(torch.float32, scale=True),
])
sample = transforms(sample)
```

Why this pattern works:
- The transform sees the whole sample at once, so random geometry is shared by image, boxes, and masks.
- `BoundingBoxes` carries `format` and `canvas_size`, which geometry transforms need to update coordinates.
- Unsupported values such as string ids pass through unchanged.
- `SanitizeBoundingBoxes` removes invalid boxes and associated fields after cropping; pass `labels_getter` for nested target layouts that the default heuristic cannot infer.

## Tuple Dataset Sample

Many datasets return `(image, target)`. Keep the same structure and wrap target fields before v2 transforms:

```python
from torchvision import tv_tensors
from torchvision.transforms import v2

class WrapDetectionSample:
    def __call__(self, image, target):
        height, width = image.shape[-2:]
        target = dict(target)
        target["boxes"] = tv_tensors.BoundingBoxes(target["boxes"], format="XYXY", canvas_size=(height, width))
        if "masks" in target:
            target["masks"] = tv_tensors.Mask(target["masks"])
        return image, target

transforms = v2.Compose([
    WrapDetectionSample(),
    v2.RandomResize(min_size=320, max_size=640),
    v2.RandomHorizontalFlip(p=0.5),
    v2.SanitizeBoundingBoxes(),
])
```

If the question is about built-in dataset wrapping rather than transform internals, route to `../../datasets-io-utils/`.

## Segmentation Masks

```python
import torch
from torchvision import tv_tensors
from torchvision.transforms import v2

image = tv_tensors.Image(torch.randint(0, 256, (3, 128, 128), dtype=torch.uint8))
mask = tv_tensors.Mask(torch.randint(0, 5, (128, 128), dtype=torch.uint8))

transforms = v2.Compose([
    v2.RandomResizedCrop((96, 96), antialias=True),
    v2.RandomHorizontalFlip(p=0.5),
    v2.ToDtype(torch.float32, scale=True),
])
image, mask = transforms(image, mask)
```

Keep segmentation masks as integer class ids. Do not normalize masks. v2 dispatches `Mask` to mask kernels so geometry applies correctly without color normalization.

## Keypoints

```python
from torchvision import tv_tensors
from torchvision.transforms import v2

keypoints = tv_tensors.KeyPoints([[[10, 20], [30, 40]]], canvas_size=(64, 80))
transforms = v2.Compose([
    v2.RandomHorizontalFlip(p=1.0),
    v2.ClampKeyPoints(),
    v2.SanitizeKeyPoints(),
])
keypoints = transforms(keypoints)
```

`KeyPoints` need `canvas_size` just like boxes. Use clamp/sanitize after geometry transforms that can move points outside the canvas.

## Videos

Use `tv_tensors.Video` or a video-shaped tensor accepted by the transform. v2 transforms generally support leading dimensions for tensor inputs, so batch/video dimensions can be preserved when the transform supports them.

```python
import torch
from torchvision import tv_tensors
from torchvision.transforms import v2

video = tv_tensors.Video(torch.randint(0, 256, (4, 3, 32, 32), dtype=torch.uint8))
transforms = v2.Compose([
    v2.Resize((24, 24), antialias=True),
    v2.UniformTemporalSubsample(2),
    v2.ToDtype(torch.float32, scale=True),
])
video = transforms(video)
```

Confirm expected video dimension order in the calling code; if the task is about video file decoding or codec behavior, route to `../../datasets-io-utils/`.

## Functionals for Shared Parameters

Use transform classes when possible. Use `torchvision.transforms.v2.functional` when parameters are already known or when implementing a custom transform:

```python
from torchvision.transforms.v2 import functional as F

image = F.resize(image, [224, 224], antialias=True)
boxes = F.resize(boxes, [224, 224], antialias=True)
```

For random behavior, sample parameters once and apply functionals to every related field. For built-in random transforms, call the transform once on the full sample instead.

## MixUp and CutMix

`v2.MixUp` and `v2.CutMix` are batch-level transforms for classification-style targets. Apply them after collation, not to a single unbatched dataset item. Keep them separate from geometry transforms that operate per sample.

## Recipe Selection

- Classification: `ToImage` -> uint8/tensor geometry -> `ToDtype(float32, scale=True)` -> `Normalize`.
- Detection: wrap `BoundingBoxes` -> geometry -> clamp/sanitize -> dtype conversion for images.
- Segmentation: wrap masks -> geometry -> image dtype conversion only.
- Keypoints: wrap with `canvas_size` -> geometry -> clamp/sanitize.
- Debugging: force deterministic transforms with `p=1.0`, small tensors, and assertion checks on output type, shape, dtype, and metadata.
