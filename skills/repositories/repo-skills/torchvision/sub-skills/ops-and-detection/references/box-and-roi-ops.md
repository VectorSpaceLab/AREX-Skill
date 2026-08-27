# Box And ROI Ops

This reference covers the low-level `torchvision.ops` APIs most often needed around detection and segmentation models.

## Coordinate and tensor conventions

- Boxes are usually floating point tensors with shape `[N, 4]`.
- `xyxy` means `[x1, y1, x2, y2]`, with top-left and bottom-right corners. Validate `x2 >= x1` and `y2 >= y1` before area, IoU, clipping, ROI, or NMS calls.
- `xywh` means `[x, y, width, height]`; convert to `xyxy` before APIs that require corner coordinates.
- `cxcywh` means `[center_x, center_y, width, height]`; convert before postprocessing.
- `box_iou` supports a `fmt` argument in current TorchVision. Prefer passing `fmt` only when every input box tensor uses that same format.
- Keep boxes, scores, labels, masks, and feature maps on the same device for composite operations.

## Box utilities

| API | Use | Inputs | Output / notes |
| --- | --- | --- | --- |
| `box_convert(boxes, in_fmt, out_fmt)` | Convert between `xyxy`, `xywh`, and `cxcywh` | `[N, 4]` boxes | Same shape in requested format |
| `box_area(boxes, fmt="xyxy")` | Compute per-box area | `[N, 4]` | `[N]`; invalid coordinate order can produce wrong areas |
| `box_iou(boxes1, boxes2, fmt="xyxy")` | Pairwise IoU | `[N, 4]`, `[M, 4]` | `[N, M]` |
| `generalized_box_iou`, `distance_box_iou`, `complete_box_iou` | IoU variants for evaluation/loss-style geometry checks | `xyxy` box tensors | `[N, M]` |
| `clip_boxes_to_image(boxes, size)` | Clamp boxes to image bounds | `size=(height, width)` | Same shape as input |
| `remove_small_boxes(boxes, min_size)` | Filter boxes with small width or height | `xyxy` boxes | Kept index tensor |
| `masks_to_boxes(masks)` | Derive boxes around binary masks | masks `[N, H, W]` | `xyxy` boxes `[N, 4]`; empty masks need explicit policy |

Validation recipe:

```python
boxes_xyxy = torchvision.ops.box_convert(boxes, in_fmt="xywh", out_fmt="xyxy")
if not torch.all(boxes_xyxy[:, 2:] >= boxes_xyxy[:, :2]):
    raise ValueError("invalid boxes: require x2 >= x1 and y2 >= y1")
```

## NMS and batched NMS

`nms(boxes, scores, iou_threshold)` returns selected indices sorted by descending score after suppressing highly overlapping `xyxy` boxes.

`batched_nms(boxes, scores, idxs, iou_threshold)` applies NMS independently per category or group id from `idxs`. Use it for class-aware postprocessing, feature-level proposal filtering, or any grouped suppression logic.

Important details:

- `boxes` shape is `[N, 4]`, `scores` shape is `[N]`, and `idxs` shape is `[N]` for `batched_nms`.
- `iou_threshold` is a float such as `0.5`; lower thresholds suppress more aggressively.
- NMS tie-breaking is not guaranteed identical between CPU and GPU when multiple boxes have the same score and satisfy the IoU criterion. Use unique scores or stable downstream assertions in tests.
- Empty inputs are valid for many box utilities, but downstream model code may still require explicit handling.

## ROI Align and ROI Pool

Functional APIs:

- `roi_align(input, boxes, output_size, spatial_scale=1.0, sampling_ratio=-1, aligned=False)`
- `roi_pool(input, boxes, output_size, spatial_scale=1.0)`
- `ps_roi_align` / `ps_roi_pool` for position-sensitive pooling variants.

Module wrappers:

- `RoIAlign(output_size, spatial_scale, sampling_ratio, aligned=False)`
- `RoIPool(output_size, spatial_scale)`
- `PSRoIAlign` and `PSRoIPool`

Accepted ROI encodings:

- A list of per-image box tensors, each shaped `[num_boxes_i, 4]`, with `xyxy` coordinates in the original image or feature-map coordinate system implied by `spatial_scale`.
- A single tensor shaped `[K, 5]` where the first column is batch index and remaining columns are `xyxy` coordinates.

Common shape checks:

- Feature input must be `[N, C, H, W]`.
- `output_size` may be an int or `(height, width)` pair.
- `spatial_scale` maps box coordinates into feature-map coordinates. For a feature map downsampled by 16, use `1.0 / 16`.
- `aligned=True` matches the common half-pixel shift variant used in modern Mask R-CNN-style implementations; keep it consistent with training/inference assumptions.

## Multi-scale ROI and FPN

`MultiScaleRoIAlign(featmap_names, output_size, sampling_ratio, canonical_scale=224, canonical_level=4)` selects an appropriate feature level for each box and runs ROI Align over a dictionary or ordered mapping of feature maps.

Use it when a detection backbone returns multiple FPN feature maps. Typical detection model code passes feature names like `['0', '1', '2', '3']`, but custom backbones must match the actual keys in the feature map dictionary.

`FeaturePyramidNetwork(in_channels_list, out_channels, extra_blocks=None, norm_layer=None)` builds a feature pyramid from ordered feature maps. It is a low-level layer; high-level model wiring belongs in `../models-and-weights/` unless the user is debugging feature-map shape/key compatibility.

## Vision losses and layers

Loss functions:

- `sigmoid_focal_loss(inputs, targets, alpha=0.25, gamma=2, reduction="none")` for dense one-vs-all classification losses.
- `generalized_box_iou_loss`, `distance_box_iou_loss`, and `complete_box_iou_loss` for box regression objectives.

Layer utilities include `FrozenBatchNorm2d`, `Conv2dNormActivation`, `Conv3dNormActivation`, `SqueezeExcitation`, `StochasticDepth`, `DropBlock2d`, `DropBlock3d`, `DeformConv2d`, `MLP`, `Permute`, and helper functions such as `deform_conv2d` and `stochastic_depth`.

Use these layers for custom heads/backbones only when the task is about operator/layer behavior. For complete model construction, route to `../models-and-weights/`.
