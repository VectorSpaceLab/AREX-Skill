# 3D WBF API reference

## Function

`weighted_boxes_fusion_3d(boxes_list, scores_list, labels_list, weights=None, iou_thr=0.55, skip_box_thr=0.0, conf_type='avg', allows_overflow=False)`

## Parameter summary

| Parameter | Meaning | Notes |
| --- | --- | --- |
| `boxes_list` | List of per-model box lists | Each box must have 6 numbers in `[x1, y1, z1, x2, y2, z2]` order. Inputs should already be normalized to `[0, 1]`. |
| `scores_list` | List of per-model confidence lists | Must align with `boxes_list`. Boxes below `skip_box_thr` are dropped before clustering. |
| `labels_list` | List of per-model label lists | Must align with `boxes_list`. Labels are numeric. The implementation casts them to `int`. |
| `weights` | Optional per-model weights | If omitted, all weights default to `1`. If the length is wrong, the implementation prints a warning and resets weights to `1`. |
| `iou_thr` | 3D IoU threshold for matching boxes | Higher values make clustering stricter. |
| `skip_box_thr` | Score threshold before clustering | Use it to discard very low-confidence boxes early. |
| `conf_type` | Confidence aggregation mode | Only `'avg'` and `'max'` are accepted in 3D. Invalid values print an error and fall back to `'avg'`. |
| `allows_overflow` | Confidence rescaling switch | `False` is the conservative default. `True` changes the post-cluster scaling rule in the implementation. |

## Return values

| Return | Shape | Meaning |
| --- | --- | --- |
| `boxes` | `(N, 6)` | Fused boxes in `[x1, y1, z1, x2, y2, z2]` order. |
| `scores` | `(N,)` | Fused confidence scores sorted from high to low. |
| `labels` | `(N,)` | Numeric labels aligned with `boxes` and `scores`. |

## Behavior notes

- Matching is label-wise: boxes only compete with other boxes that share the same label.
- `x2 < x1`, `y2 < y1`, or `z2 < z1` are swapped internally with warnings.
- Coordinates outside `[0, 1]` are clipped with warnings.
- Zero-volume boxes are skipped.
- When `allows_overflow` is `False`, the implementation rescales each cluster by `min(weights.sum(), cluster_size) / weights.sum()`.
- When `allows_overflow` is `True`, the implementation rescales each cluster by `cluster_size / weights.sum()`.
- If all boxes are filtered out, the function returns empty arrays with shapes `(0, 6)`, `(0,)`, and `(0,)`.
- There are no 3D NMS, Soft-NMS, or non-maximum-weighted wrappers in this package.
