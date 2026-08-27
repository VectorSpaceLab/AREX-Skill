# Workflow recipes

## 1. Pick the method

| Need | Prefer | Why |
| --- | --- | --- |
| Fuse overlapping detector outputs into one coordinate set | `weighted_boxes_fusion` | Best default when you want a single consensus box per object. |
| Fuse boxes but keep a more conservative score model | `box_and_model_avg` or `absent_model_aware_avg` | Helps when one model emits repeated duplicates or when not every model fires. |
| Keep the strongest box and suppress the rest | `nms` | Simple hard suppression. |
| Decay nearby duplicates instead of deleting them | `soft_nms` | Retains more hypotheses for downstream filtering. |
| Keep a weighted representative box without full WBF confidence logic | `non_maximum_weighted` | Good when overlap-weighted selection is enough. |
| Use the faster vectorized WBF path | `weighted_boxes_fusion_experimental` | Only after inputs are already trusted and normalized. |

## 2. Standard multi-model 2D fusion

1. Convert every model's predictions into the same image frame.
2. Normalize all boxes to `[0, 1]` and order them as `[x1, y1, x2, y2]`.
3. Keep `boxes_list`, `scores_list`, and `labels_list` aligned per model.
4. Provide one model weight per model if you want weighted voting.
5. Choose `iou_thr` for clustering and `skip_box_thr` for low-score filtering.
6. Choose a confidence mode:
   - `avg` for a plain default;
   - `max` for peak-confidence retention;
   - `box_and_model_avg` when repeated boxes from one model would otherwise dominate;
   - `absent_model_aware_avg` for a more conservative score when some models do not fire.
7. Validate that the output arrays are sorted by score and that labels still match the class IDs you expect.

Example:

```python
from ensemble_boxes import weighted_boxes_fusion

boxes, scores, labels = weighted_boxes_fusion(
    boxes_list,
    scores_list,
    labels_list,
    weights=[1.0, 1.0, 1.0],
    iou_thr=0.55,
    skip_box_thr=0.0,
    conf_type="box_and_model_avg",
    allows_overflow=False,
)
```

## 3. Merge YOLO, Faster R-CNN, and DetectoRS outputs

- Convert each detector's output format into the shared normalized box format.
- Preserve per-model grouping. Do not flatten everything before calling the API.
- If a detector produces no boxes, keep its entry as an empty list so the model count stays aligned.
- Use model weights to reflect detector trust, validation score, or calibration quality.
- Start with `iou_thr=0.5` to `0.55`, then tune on a small validation set.

## 4. Handle repeated boxes from one model

Use this pattern when one detector emits multiple near-duplicates around the same object:

- `avg` can still work, but the score can look too high when the cluster is dominated by one model.
- `box_and_model_avg` rescales by the number of unique models that contributed.
- `absent_model_aware_avg` adds another penalty for models that did not contribute.
- Keep `allows_overflow=False` unless you explicitly want scores above `1.0`.

## 5. Normalize raw pixel boxes first

If your model outputs pixel coordinates, normalize before calling the library:

```python
import numpy as np

def normalize_xyxy(boxes_px, width, height):
    boxes = np.asarray(boxes_px, dtype=np.float32).copy()
    boxes[:, [0, 2]] /= float(width)
    boxes[:, [1, 3]] /= float(height)
    boxes[:, [0, 2]] = np.sort(boxes[:, [0, 2]], axis=1)
    boxes[:, [1, 3]] = np.sort(boxes[:, [1, 3]], axis=1)
    np.clip(boxes, 0.0, 1.0, out=boxes)
    return boxes
```

This keeps the caller in control of image geometry. The library can clip and swap
corners, but it does not know the original image size.

## 6. Experimental fast path

1. Sanitize and normalize inputs first.
2. Compare the experimental output against standard WBF on a small validation
   sample with a small numeric tolerance.
3. Only then consider `skip_checks=True`.
4. If confidence behavior matters more than speed, stay on the standard WBF path.

## 7. Single-model fallback

You can still use the same APIs when only one model is available. Wrap the model
arrays in an outer list and keep the same input contract:

```python
boxes, scores, labels = weighted_boxes_fusion(
    [boxes_list],
    [scores_list],
    [labels_list],
    weights=[1.0],
)
```

## 8. Minimal validation pass

After any fusion or suppression call, check:

- output shapes are correct;
- boxes are within `[0, 1]`;
- labels are numeric and map back to your classes;
- scores are sorted in descending order;
- the chosen method matches the task intent.
