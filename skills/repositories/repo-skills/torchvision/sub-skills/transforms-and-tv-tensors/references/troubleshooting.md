# Troubleshooting

## Wrong Dtype or Range

Symptoms:
- `Normalize` outputs extreme values.
- Model accuracy collapses after migrating transforms.
- Images look black, white, or saturated.

Fixes:
- Float image tensors should normally be in `[0, 1]`.
- `torch.uint8` image tensors should normally be in `[0, 255]`.
- Use `v2.ToDtype(torch.float32, scale=True)` before `v2.Normalize(...)`.
- Do not normalize masks, labels, boxes, or keypoints.

```python
pipeline = v2.Compose([
    v2.ToImage(),
    v2.ToDtype(torch.float32, scale=True),
    v2.Normalize(mean, std),
])
```

If a float tensor is already `[0, 255]`, convert deliberately before normalization; do not assume `Normalize` rescales.

## Lost Bounding Box Metadata

Symptoms:
- `target["boxes"]` becomes a plain `torch.Tensor`.
- Geometry transforms stop updating boxes.
- Code later cannot read `.format` or `.canvas_size`.

Causes:
- Native `torch` arithmetic on TVTensors often unwraps them.
- A custom transform returned a plain tensor.
- Boxes were never wrapped as `tv_tensors.BoundingBoxes`.

Fixes:

```python
from torchvision import tv_tensors

boxes = tv_tensors.BoundingBoxes(boxes, format="XYXY", canvas_size=(height, width))
boxes = tv_tensors.wrap(boxes + 1, like=boxes)
```

In custom `v2.Transform` code, return `tv_tensors.wrap(output, like=input_boxes)` for modified boxes.

## Missing `canvas_size`

Symptoms:
- Constructing `BoundingBoxes` or `KeyPoints` fails.
- Resize, crop, flip, or affine transforms cannot update annotations correctly.

Fixes:
- Always pass `canvas_size=(height, width)`.
- Derive it from the paired image as `image.shape[-2:]` after image loading but before geometry transforms.
- Update or recreate annotation TVTensors if you manually resize outside v2.

```python
height, width = image.shape[-2:]
target["boxes"] = tv_tensors.BoundingBoxes(target["boxes"], format="XYXY", canvas_size=(height, width))
```

## Wrong Box Format

Symptoms:
- Boxes appear mirrored, shifted, too large, or invalid after transforms.
- IoU or NMS results are nonsensical.

Fixes:
- Identify whether input is `XYXY`, `XYWH`, or `CXCYWH`.
- Set the correct format when constructing `BoundingBoxes`.
- Convert explicitly before downstream code that assumes one format.

```python
pipeline = v2.Compose([
    v2.ConvertBoundingBoxFormat("XYXY"),
    v2.ClampBoundingBoxes(),
    v2.SanitizeBoundingBoxes(),
])
```

Do not relabel `XYWH` values as `XYXY`; convert them.

## PIL and Tensor Backend Mismatch

Symptoms:
- Slight numeric differences after migration.
- Transform accepts PIL in one path but tensor in another.
- Performance differs sharply between local debugging and training.

Fixes:
- Prefer tensor-first v2 pipelines for consistency and speed.
- Put `v2.ToImage()` at the start when inputs may be PIL.
- Use explicit `InterpolationMode` and `antialias=True` for resize/crop transforms.
- Keep final conversion to float and normalization after geometry.

## Random Transform Determinism

Symptoms:
- Image and boxes no longer align.
- Re-running a debug case gives different outputs.
- A custom random transform moves masks differently from images.

Fixes:
- Call the transform once on the full sample, not separately on fields.
- For debugging, set `torch.manual_seed(...)` immediately before the transform call.
- In custom `v2.Transform`, sample random choices in `make_params(flat_inputs)`, not separately in each `transform()` call.
- Use `p=1.0` while validating geometry effects.

## Boxes or Keypoints Disappear After Crop

Symptoms:
- Empty targets after `RandomIoUCrop`, crop, affine, or perspective transforms.
- Labels no longer match boxes.

Fixes:
- Use `v2.SanitizeBoundingBoxes()` after geometry crops.
- Use `v2.ClampBoundingBoxes()` if boxes should be clipped to the canvas.
- Use `v2.SanitizeKeyPoints()` or `v2.ClampKeyPoints()` for keypoint pipelines.
- Confirm labels are in a structure supported by the sanitizing transform for coupled filtering.

## TorchScript Constraints

Symptoms:
- `torch.jit.script(v2.Compose(...))` fails.
- Scripted output differs from eager v2 output.
- Scripted functionals treat boxes as images.

Fixes:
- Use `torch.nn.Sequential` for simple scriptable tensor-only transform modules.
- Prefer scripting v2 functionals for pure tensor image paths.
- Use low-level kernels for scripted non-image types such as bounding boxes or masks.
- Keep arbitrary nested Python samples in eager preprocessing, not scripted model graphs.

## Performance Pitfalls

Symptoms:
- Data loading is slower after migration.
- CPU usage is high with low GPU utilization.
- Resize dominates preprocessing time.

Fixes:
- Prefer tensor inputs over PIL images.
- Keep images as `torch.uint8` through resize-heavy geometry, then convert to float once.
- Use v2 transforms instead of v1 for new code.
- Use bilinear or bicubic resize modes where suitable.
- Benchmark `DataLoader(num_workers > 0)` and avoid doing expensive transforms in the model forward pass.
- Avoid unnecessary global `tv_tensors.set_return_type("TVTensor")` in hot paths.

## Quick Diagnostic Assertions

```python
from torchvision import tv_tensors

assert image.shape[-2:] == target["boxes"].canvas_size
assert isinstance(target["boxes"], tv_tensors.BoundingBoxes)
assert target["boxes"].ndim >= 2 and target["boxes"].shape[-1] in {4, 5, 6, 8}
assert image.dtype in {torch.uint8, torch.float32}
```

Use the bundled `scripts/smoke_transform_pipeline.py` as a minimal no-download reference for metadata-preserving behavior.
