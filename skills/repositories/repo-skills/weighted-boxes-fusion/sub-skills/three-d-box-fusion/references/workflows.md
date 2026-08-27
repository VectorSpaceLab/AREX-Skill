# 3D WBF workflows

## 1) Fuse normalized 3D detector outputs

Use this when several models predict the same axis-aligned cuboids in a shared normalized frame.

1. Collect one box list, score list, and label list per model.
2. Keep the coordinate order as `[x1, y1, z1, x2, y2, z2]`.
3. Make sure every coordinate is normalized to `[0, 1]` before fusion.
4. Pick a 3D IoU threshold and a score cutoff.
5. Choose `conf_type='avg'` for the default ensemble score, or `conf_type='max'` when you want the best contributor score to dominate.
6. Fuse and validate the arrays.

```python
from ensemble_boxes import weighted_boxes_fusion_3d

boxes, scores, labels = weighted_boxes_fusion_3d(
    boxes_list,
    scores_list,
    labels_list,
    weights=[1.0, 1.0],
    iou_thr=0.55,
    skip_box_thr=0.0,
    conf_type="avg",
    allows_overflow=False,
)

assert boxes.shape[1] == 6
assert len(boxes) == len(scores) == len(labels)
```

## 2) Normalize metric cuboids first

Use this when your boxes come from LiDAR, MRI, CT, or other metric coordinate systems.

- Normalize each axis to the same shared scene or volume range before calling WBF.
- Preserve axis ordering: x stays x, y stays y, z stays z.
- Apply the same per-axis affine map to both corners of each box.
- If you need metric outputs again, de-normalize the fused boxes with the same map after fusion.

Generic normalization pattern:

```python
x1 = (x1 - x_min) / (x_max - x_min)
y1 = (y1 - y_min) / (y_max - y_min)
z1 = (z1 - z_min) / (z_max - z_min)
x2 = (x2 - x_min) / (x_max - x_min)
y2 = (y2 - y_min) / (y_max - y_min)
z2 = (z2 - z_min) / (z_max - z_min)
```

## 3) Choose the confidence mode

- `avg`: best default for most 3D ensembling tasks.
- `max`: use when a single strong detector should dominate the fused score.
- Unsupported names such as `absent_model_aware_avg` are not available in 3D. Use `avg` or `max` only.

If the user supplies an invalid string, the implementation prints an error and falls back to `avg`.

## 4) Validate the outputs

After fusion, check:

- `boxes.shape == (N, 6)`
- `len(boxes) == len(scores) == len(labels)`
- every coordinate is still in `[0, 1]`
- `x1 <= x2`, `y1 <= y2`, `z1 <= z2`
- `labels` are the expected numeric class ids

If the task needs class names, map them to numeric ids before fusion and map them back afterward.

## 5) Decide whether overflow is acceptable

- Leave `allows_overflow=False` when you want the conservative default scaling.
- Set `allows_overflow=True` only if your downstream logic expects the implementation's alternate confidence rescaling rule.

The smoke script in [scripts/smoke_3d_fusion.py](../scripts/smoke_3d_fusion.py) exercises the common happy path, the invalid-confidence fallback, and the zero-volume skip case.
