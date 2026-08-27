# API reference

This reference covers the 2D prediction-ensembling entry points in
`ensemble_boxes`.

## 2D input contract

All 2D functions in this sub-skill expect normalized boxes in the form
`[x1, y1, x2, y2]` with values in `[0, 1]`.

| Input | Shape | Notes |
| --- | --- | --- |
| `boxes_list` | list of models, each a list of boxes | Keep one outer entry per model, even when a model has no boxes. |
| `scores_list` | list of models, each a list of scores | Must stay aligned with `boxes_list`. |
| `labels_list` | list of models, each a list of numeric labels | Must stay aligned with `boxes_list`. |
| `weights` | list of model weights | Optional. Length should match the number of models. |

Output arrays are returned sorted by descending confidence:

| Output | Shape | Notes |
| --- | --- | --- |
| `boxes` | `(N, 4)` | Fused or selected boxes in `[x1, y1, x2, y2]` order. |
| `scores` | `(N,)` | Confidence scores after fusion or suppression. |
| `labels` | `(N,)` | Numeric labels. Cast to `int` if your caller expects integers. |

## Function signatures

| Function | Role | Signature |
| --- | --- | --- |
| `weighted_boxes_fusion` | Default 2D WBF entry point | `weighted_boxes_fusion(boxes_list, scores_list, labels_list, weights=None, iou_thr=0.55, skip_box_thr=0.0, conf_type='avg', allows_overflow=False)` |
| `weighted_boxes_fusion_experimental` | Vectorized 2D WBF variant | `weighted_boxes_fusion_experimental(boxes_list, scores_list, labels_list, weights=None, iou_thr=0.55, skip_box_thr=0.0, conf_type='avg', allows_overflow=False, skip_checks=False)` |
| `non_maximum_weighted` | Weighted cluster suppression | `non_maximum_weighted(boxes_list, scores_list, labels_list, weights=None, iou_thr=0.55, skip_box_thr=0.0)` |
| `nms_method` | Shared engine for standard and soft NMS | `nms_method(boxes, scores, labels, method=3, iou_thr=0.5, sigma=0.5, thresh=0.001, weights=None)` |
| `nms` | Standard NMS wrapper | `nms(boxes, scores, labels, iou_thr=0.5, weights=None)` |
| `soft_nms` | Soft-NMS wrapper | `soft_nms(boxes, scores, labels, method=2, iou_thr=0.5, sigma=0.5, thresh=0.001, weights=None)` |

## Confidence modes

### `weighted_boxes_fusion`

| `conf_type` | Meaning | When to use |
| --- | --- | --- |
| `avg` | Plain average over clustered boxes | Default when each object is usually predicted once per model. |
| `max` | Maximum score in the cluster | When you want the strongest detector to dominate. |
| `box_and_model_avg` | Box average plus unique-model rescaling | Useful when repeated boxes from the same model would otherwise inflate the score. |
| `absent_model_aware_avg` | Conservative rescaling that also accounts for absent models | Best when only a subset of models fires on an object. |

`allows_overflow=False` keeps the final confidence capped more conservatively.
With repeated detections from one model, the special averaging modes are usually
safer than plain `avg`.

### `weighted_boxes_fusion_experimental`

- Same confidence modes as standard WBF.
- Expect small numeric drift versus standard WBF because this path is more
  vectorized.
- `skip_checks=False` keeps the input validation path enabled.
- `skip_checks=True` disables the shape/range/zero-area checks and should only be
  used after the caller has already normalized and sanitized the inputs.

## Method mapping for `nms_method`

| `method` | Behavior |
| --- | --- |
| `1` | Linear Soft-NMS |
| `2` | Gaussian Soft-NMS |
| `3` | Standard NMS |

`sigma` only affects Gaussian Soft-NMS. `thresh` is the post-decay score cutoff.

## Weight behavior

- `weights=None` means every model starts with weight `1`.
- For WBF and NMW, a length mismatch resets the weights to all ones.
- For `nms_method`, `nms`, and `soft_nms`, a length mismatch leaves the original
  boxes in place and ignores the bad weight list.
- Keep one weight per model, not one weight per box.

## Validation notes

- Standard WBF and NMW clip coordinates to `[0, 1]`, swap reversed corners, and
  skip zero-area boxes.
- The experimental WBF path can skip these checks when `skip_checks=True`.
- Empty per-model lists are fine as long as the outer model list still stays
  aligned.
