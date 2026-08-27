# Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Fused spans are empty or disappear | The span endpoints were not normalized, were reversed, or collapsed to zero length after clipping; the library also skips zero-length segments. | Normalize to `[0, 1]`, sort endpoints so `x1 <= x2`, and make sure the converted span still covers at least one token or character. |
| A span is missing before clustering | `skip_box_thr` removed it because the score was too low. | Lower `skip_box_thr`, or check whether you accidentally scaled the scores twice. |
| Spans refuse to merge | `iou_thr` is too high, or the intervals barely overlap. | Lower `iou_thr` until the intended candidates cluster together. |
| Labels come back as numbers | The API works on numeric labels; string classes are not preserved automatically. | Use a shared `class_to_label` map before fusion and a `label_to_class` reverse map after fusion. |
| Labels end up in the wrong class | Different models used different class-to-id mappings. | Rebuild every model's `labels_list` from one stable label map. |
| The process exits with `Unknown conf_type` | `conf_type` is not one of the accepted values. | Use `avg`, `max`, `box_and_model_avg`, or `absent_model_aware_avg`. |
| Coordinates are clipped or swapped | Inputs were outside `[0, 1]` or the endpoints were reversed. | Normalize first, then let the cleanup step clip out-of-range values and swap reversed endpoints. |
| Weights appear ignored | The weight list length does not match the number of models, so the library resets weights to ones. | Provide exactly one weight per model in the same order as `boxes_list`. |

## Quick diagnosis for disappearing fused spans

If the final fused result is empty, check these in order:

1. Did the span survive normalization?
2. Did `skip_box_thr` filter it out before clustering?
3. Did label mapping put it under a different numeric class?
4. Did clipping collapse the interval to zero length?
5. Is `iou_thr` too strict for the actual overlap pattern?

## Quick diagnosis for NER-style inputs

If you start from `predictionstring` values:

- Make sure each `predictionstring` is non-empty.
- Convert token ids to normalized `[x1, x2]` spans before fusion.
- Convert the fused output back to inclusive token ids after fusion.
- Do not feed raw token ids directly into the API.
