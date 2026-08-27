# Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Printed length error for boxes, scores, or labels | One model's `boxes`, `scores`, and `labels` lists do not have the same length | Fix the per-model triplets before calling the API. WBF and NMW exit on this mismatch; `nms_method` skips the bad model entry. |
| Coordinates outside `[0, 1]`, reversed corners, or zero-area boxes | Raw pixel inputs were passed directly, or corners were not ordered | Normalize first, then sort x and y corners. Standard WBF and NMW will clip and swap for you, but the caller should still provide a common normalized coordinate system. Zero-area boxes are skipped. |
| Weight list was ignored or reset | `weights` length does not match the model count | Provide one weight per model. WBF and NMW reset to all ones; the NMS path warns and ignores the invalid weight list. |
| `Unknown conf_type` followed by `SystemExit` | An unsupported confidence mode was passed to WBF or the experimental WBF path | Use `avg`, `max`, `box_and_model_avg`, or `absent_model_aware_avg`. Catch `SystemExit` only if you are intentionally probing bad inputs in a notebook or test. |
| Some models are empty and NMS still works | Empty per-model lists are allowed as long as at least one model has boxes | Keep empty models as empty lists so alignment stays intact. If every model is empty, guard in the caller and return empty arrays yourself. |
| Scores rise above `1.0` or one model dominates a repeated cluster | Plain `avg` with duplicate boxes from the same model, or `allows_overflow=True` | Keep `allows_overflow=False`. When duplicate boxes from one model are common, switch to `box_and_model_avg` or `absent_model_aware_avg`. |
| Soft-NMS removes too many boxes | `thresh` is too high or `sigma` is too small | Lower `thresh` or raise `sigma`, then re-check the score ordering. |
| Experimental WBF differs from standard WBF | Inputs were not fully sanitized, or you used `skip_checks=True` too early | Compare against standard WBF first. Use `skip_checks=True` only after the caller already normalizes and validates the inputs. |

## Fast recovery checklist

1. Check each model's list lengths.
2. Check that every box is normalized and ordered.
3. Check that `weights` matches the model count.
4. Check the chosen `conf_type`.
5. Check whether the task needs WBF, NMW, NMS, or Soft-NMS.

For repeated same-model boxes, the safest default is usually:

- `conf_type="box_and_model_avg"`
- `allows_overflow=False`
- `iou_thr` tuned on a small validation sample
