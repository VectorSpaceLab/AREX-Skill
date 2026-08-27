# Ops And Detection Troubleshooting

Use this guide for failures around `torchvision.ops`, detection helper shapes, custom C++ ops, and postprocessing behavior.

## `operator torchvision::nms does not exist`

Likely causes:

- PyTorch and TorchVision wheels are from incompatible release or CUDA/CPU build families.
- TorchVision was imported from a source tree or partial install where the compiled `_C` extension was not built.
- A CPU-only PyTorch install is paired with a CUDA TorchVision wheel, or the reverse.
- Import is resolving to a different environment than the one where TorchVision was installed.

Checks:

```python
import torch, torchvision
print(torch.__version__)
print(torchvision.__version__)
from torchvision import extension
print(extension._has_ops())
```

Action:

1. Reinstall matching PyTorch and TorchVision packages from the same release channel and hardware family.
2. If building from source, rebuild TorchVision after PyTorch is installed and ensure the compiled extension is on the import path.
3. Set `TORCHVISION_WARN_WHEN_EXTENSION_LOADING_FAILS=1` before import to surface extension loading warnings.
4. Re-run `scripts/smoke_ops.py` to confirm `nms` and `roi_align` execute on tiny CPU tensors.

## Custom C++ ops unavailable

TorchVision raises a custom-ops error when `_has_ops()` is false and a compiled operator is required. The error usually points to version mismatch or source build problems.

Do not fix this by replacing `nms` with ad hoc Python code unless the task explicitly needs a fallback for a constrained environment. Prefer fixing the install, because detection models also depend on compiled ops.

## PyTorch / TorchVision version mismatch

Symptoms include missing operators, undefined symbols, extension load warnings, CUDA major-version errors, or import-time failures.

Checklist:

- Compare `torch.__version__` and `torchvision.__version__` against the official compatibility matrix for the release family.
- Confirm both packages are CPU-only or both use the intended CUDA runtime family.
- Remove stale editable/source installs if Python imports a different TorchVision than the package manager reports.
- Avoid mixing nightly and stable packages unless both are from matching nightly indexes.

## CPU/GPU device mismatch

Typical errors mention tensors on different devices. Composite code often moves images/features to CUDA but leaves boxes, scores, or labels on CPU.

Fix pattern:

```python
device = feature_map.device
boxes = boxes.to(device)
scores = scores.to(device)
labels = labels.to(device)
keep = torchvision.ops.batched_nms(boxes, scores, labels, 0.5)
```

For ROI ops, move both the feature input and ROI boxes to compatible devices. If boxes are a list, move every tensor in the list.

## Invalid box coordinate order

Symptoms include negative areas, unexpected IoU, NMS keeping/suppressing the wrong boxes, empty detections, or ROI shape failures.

Validate before ops:

```python
if boxes.numel() and not torch.all(boxes[:, 2:] >= boxes[:, :2]):
    raise ValueError("boxes must be xyxy with x2 >= x1 and y2 >= y1")
```

If source annotations are `xywh` or `cxcywh`, convert with `box_convert` before IoU, clipping, ROI, or NMS.

## NMS nondeterminism with ties

When several boxes have the same score and overlap above the threshold, the selected index among ties may differ across CPU and GPU. This mirrors sorting/selection behavior and should not be treated as a semantic model difference.

Mitigations:

- Avoid exact score ties in tests by adding tiny deterministic score offsets.
- Assert the set size, score thresholding, and coordinate validity rather than exact index order when ties exist.
- For production postprocessing, make tie policy explicit upstream if stable ordering is required.

## ROI Align / Pool shape errors

Common causes:

- Feature input is not rank 4 `[N, C, H, W]`.
- ROI tensor is `[K, 4]` when functional call expects a list or `[K, 5]` with batch index.
- `output_size` is malformed; use an int or `(height, width)` pair.
- `spatial_scale` does not match feature-map stride, producing crops from the wrong region.
- `MultiScaleRoIAlign.featmap_names` does not match the keys returned by the backbone.
- Boxes are in resized image coordinates while features correspond to a different scale.

Debug sequence:

1. Print feature map keys and shapes.
2. Validate every ROI box has `xyxy` order and non-negative extent.
3. Confirm the number of per-image box lists matches batch size.
4. Check `featmap_names` exactly match available feature keys.
5. Run a tiny `roi_align` call on one feature map and one box before debugging the full model.

## Empty detections

Empty output is often valid. Check these before assuming an op bug:

- `score_thresh` may be too high.
- `remove_small_boxes` may filter all candidates.
- NMS threshold may be too low for crowded objects.
- Boxes may be outside image bounds before clipping.
- Model is in training mode, where detection models return losses instead of final predictions.

## Smoke script interpretation

`scripts/smoke_ops.py` uses tiny CPU tensors and should finish quickly. Results:

- `ok`: import, box conversion, IoU, NMS, and ROI Align worked.
- `missing-ops`: import succeeded but compiled operators are unavailable or an op is not registered.
- `failed`: an unexpected error occurred; inspect the printed exception and versions.

The script is intentionally small and offline-safe. It does not validate model accuracy or GPU kernels.
