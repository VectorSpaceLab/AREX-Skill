# API reference

## `weighted_boxes_fusion_1d`

```python
weighted_boxes_fusion_1d(
    boxes_list,
    scores_list,
    labels_list,
    weights=None,
    iou_thr=0.55,
    skip_box_thr=0.0,
    conf_type='avg',
    allows_overflow=False,
)
```

### Expected inputs

| argument | shape / type | notes |
| --- | --- | --- |
| `boxes_list` | `list[list[list[float]]]` | One outer item per model; each inner item is an `[x1, x2]` span. Coordinates must be normalized to `[0, 1]`. |
| `scores_list` | `list[list[float]]` | Same inner lengths as the matching `boxes_list` item. |
| `labels_list` | `list[list[int]]` | Numeric labels only. Cast string classes to ints before calling. |
| `weights` | `list[float]` or `None` | Defaults to one weight per model. A length mismatch resets all weights to ones with a warning. |
| `iou_thr` | `float` | Interval IoU threshold for clustering spans. Higher values merge fewer spans. |
| `skip_box_thr` | `float` | Candidate spans with score below this threshold are removed before clustering. |
| `conf_type` | `str` | One of `avg`, `max`, `box_and_model_avg`, `absent_model_aware_avg`. Invalid values terminate with an error. |
| `allows_overflow` | `bool` | Uses the capped rescaling path when `False`; allows the more permissive overflow-style rescaling branch when `True`. |

### Returns

- `boxes`: `ndarray` with shape `(N, 2)`.
- `scores`: `ndarray` with shape `(N,)`.
- `labels`: `ndarray` with numeric labels.

### Behavior notes

- The function groups spans by label internally.
- Reversed endpoints are swapped, values outside `[0, 1]` are clipped, and zero-length spans are skipped before clustering.
- `labels` stay numeric through the API; reverse-map them to class strings after fusion if your downstream format needs names.
- Use `iou_thr` to control how aggressively intervals merge.

### Interval IoU

For spans `[a1, a2]` and `[b1, b2]`:

```text
intersection = max(0, min(a2, b2) - max(a1, b1))
iou = intersection / ((a2 - a1) + (b2 - b1) - intersection)
```

### Confidence modes

| mode | summary |
| --- | --- |
| `avg` | Safe default; averages the fused confidence. |
| `max` | Keeps the strongest contributing score. |
| `box_and_model_avg` | Adjusts by both the number of boxes in the cluster and model weights. |
| `absent_model_aware_avg` | Penalizes missing-model coverage in the cluster. |

### Round-trip mapping pattern

Use a shared map for every model, then convert the fused output back to strings after `weighted_boxes_fusion_1d` finishes:

```python
class_to_label = {"Claim": 0, "Evidence": 1}
label_to_class = {v: k for k, v in class_to_label.items()}
```

This lets you feed the function numeric labels while still returning string classes or `predictionstring` rows downstream.
