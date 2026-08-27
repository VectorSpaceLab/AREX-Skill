# TVTensors and Annotations

`torchvision.tv_tensors` are `torch.Tensor` subclasses used by v2 transforms to dispatch inputs to the right kernels. Most application code only needs to construct them at dataset boundaries or before calling a v2 transform pipeline.

## Available TVTensor Types

| Type | Use | Required metadata |
| --- | --- | --- |
| `tv_tensors.Image` | Image tensors or PIL images | Shape carries size |
| `tv_tensors.Video` | Video tensors | Shape carries frame/spatial dimensions |
| `tv_tensors.Mask` | Detection or segmentation masks | Shape carries size |
| `tv_tensors.BoundingBoxes` | Axis-aligned or rotated boxes | `format`, `canvas_size` |
| `tv_tensors.KeyPoints` | Keypoint coordinates | `canvas_size` |
| `tv_tensors.TVTensor` | Base class for advanced use | Type-specific |

## Constructing Annotation Tensors

```python
import torch
from torchvision import tv_tensors

height, width = 64, 80
image = tv_tensors.Image(torch.randint(0, 256, (3, height, width), dtype=torch.uint8))
boxes = tv_tensors.BoundingBoxes(
    torch.tensor([[4, 5, 30, 40], [10, 20, 50, 60]], dtype=torch.float32),
    format="XYXY",
    canvas_size=(height, width),
)
mask = tv_tensors.Mask(torch.zeros((2, height, width), dtype=torch.uint8))
keypoints = tv_tensors.KeyPoints(torch.tensor([[[12, 18], [25, 30]]], dtype=torch.float32), canvas_size=(height, width))
```

Use `(height, width)` for `canvas_size`, matching `image.shape[-2:]`.

## Bounding Box Formats

Common formats include:

- `XYXY`: `[xmin, ymin, xmax, ymax]`.
- `XYWH`: `[xmin, ymin, width, height]`.
- `CXCYWH`: `[center_x, center_y, width, height]`.

Use `v2.ConvertBoundingBoxFormat("XYXY")` when downstream code expects a particular format. Keep the format in the TVTensor metadata instead of relying on variable names.

```python
from torchvision.transforms import v2

pipeline = v2.Compose([
    v2.ConvertBoundingBoxFormat("XYXY"),
    v2.ClampBoundingBoxes(),
    v2.SanitizeBoundingBoxes(),
])
```

Rotated boxes are represented through supported rotated bounding box formats in the current torchvision version. Preserve their declared format and canvas size and prefer v2 transform APIs that explicitly support rotated boxes.

## Metadata Preservation Rules

- Built-in v2 transforms and v2 functionals return the same supported type they receive, including `BoundingBoxes` metadata after geometry updates.
- Native `torch` operations usually unwrap TVTensors to plain tensors for performance.
- Operations such as `.clone()`, `.to()`, `.detach()`, and `.requires_grad_()` preserve TVTensor type.
- In-place operations keep the object type, but their returned value can be a plain tensor.

When a custom transform uses tensor arithmetic, re-wrap outputs:

```python
from torchvision import tv_tensors

new_boxes = boxes + 3
new_boxes = tv_tensors.wrap(new_boxes, like=boxes)
```

Use `tv_tensors.set_return_type("TVTensor")` sparingly. It is global or context-scoped behavior and can add overhead or surprise model code.

## Arbitrary Sample Structures

v2 transforms preserve the structure of inputs and only transform supported objects:

```python
sample = {
    "image": image,
    "annotations": {
        "boxes": boxes,
        "labels": torch.tensor([1, 2]),
        "masks": mask,
    },
    "path": "kept-for-debugging",
}
sample = transforms(sample)
```

Plain labels, ids, strings, and unsupported objects pass through. If there is an `Image`, `Video`, or PIL image in the sample, additional plain tensors are usually treated as pass-through metadata rather than images. If there is no image-like object, the first pure tensor can be interpreted as an image. Wrap images explicitly with `tv_tensors.Image` when the sample contains many plain tensors.

## Custom Transform Pattern

For fixed input structures, a normal `torch.nn.Module` with `forward()` can be enough. For transform behavior over arbitrary nested inputs, subclass `v2.Transform` and implement `transform()` and optionally `make_params()`:

```python
from typing import Any
import torch
from torchvision import tv_tensors
from torchvision.transforms import v2

class ShiftBoxes(v2.Transform):
    def transform(self, inpt: Any, params):
        if isinstance(inpt, tv_tensors.BoundingBoxes):
            return tv_tensors.wrap(inpt + 1, like=inpt)
        return inpt
```

For random custom transforms, sample once in `make_params(flat_inputs)` and reuse the result in every `transform()` call so images and annotations stay synchronized.

## Annotation Integrity Checks

Add assertions around difficult pipelines:

```python
assert isinstance(target["boxes"], tv_tensors.BoundingBoxes)
assert target["boxes"].canvas_size == image.shape[-2:]
assert str(target["boxes"].format).upper().endswith("XYXY")
assert target["masks"].shape[-2:] == image.shape[-2:]
```

After crops, random IoU crops, affine transforms, or perspective transforms, inspect whether boxes or keypoints can leave the canvas. Use clamp/sanitize transforms before passing annotations to a model or loss.
