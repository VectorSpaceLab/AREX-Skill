# Workflow recipes

## 1. Fuse token spans from multiple NLP models

Use this pattern when each model emits span predictions in `predictionstring` style or token-index spans.

1. Build a stable label map once and reuse it across all models.

   ```python
   class_to_label = {"Claim": 0, "Evidence": 1}
   label_to_class = {v: k for k, v in class_to_label.items()}
   ```

2. Convert each model's spans into normalized intervals.
   - For a token span `[start_token, end_token]`, divide both endpoints by a shared `max_box_value`.
   - Use `max_box_value = max_token_index + 1` for Feedback Prize style token indices.
   - Keep the order `[x1, x2]` and ensure the values stay in `[0, 1]`.

3. Build the three parallel inputs expected by `weighted_boxes_fusion_1d`:
   - `boxes_list`: list of normalized spans per model.
   - `scores_list`: confidence scores per model.
   - `labels_list`: numeric class ids per model.

4. Fuse the spans.

   ```python
   boxes, scores, labels = weighted_boxes_fusion_1d(
       boxes_list,
       scores_list,
       labels_list,
       weights=[1.0] * len(boxes_list),
       iou_thr=0.33,
       skip_box_thr=0.0,
       conf_type="avg",
   )
   ```

5. Convert each fused interval back to token indices.
   - `start = ceil(x1 * max_box_value)`
   - `end = int(x2 * max_box_value)`
   - Rebuild the inclusive `predictionstring` with `range(start, end + 1)`.

6. Reverse-map numeric labels to class strings.

### Practical defaults
- Start with `iou_thr=0.33` for overlapping token spans.
- Use `skip_box_thr` only after you know every model is producing scores on the same scale.
- Keep `conf_type="avg"` until you have a reason to prefer a benchmark-style rescaling mode.

## 2. Fuse spans that are already normalized

Use this when the upstream model already outputs `[x1, x2]` intervals in `[0, 1]`.

- Do not normalize twice.
- Keep every model on the same scale.
- If spans come from integer token ids or character offsets, normalize them once before fusion.
- If a span would become empty after conversion, drop it before the fusion call so the cleanup step is explicit.

## 3. Tune the main knobs

| knob | move it lower when... | move it higher when... |
| --- | --- | --- |
| `iou_thr` | spans should merge more aggressively | spans are over-merging or absorbing nearby noise |
| `skip_box_thr` | valid spans are being filtered out | too many weak candidates survive preprocessing |
| `weights` | one model should count less | one model is consistently stronger |
| `conf_type` | you want a simple default | you need more benchmark-oriented rescoring |
| `allows_overflow` | you want the capped rescaling path | you explicitly want the overflow-style branch |

## 4. Deterministic round-trip for `predictionstring`

Use this when your source labels are strings and the downstream format expects string classes plus inclusive token spans.

```python
max_box_value = max_token_index + 1
start_token = int(tokens[0])
end_token = int(tokens[-1])
box = [start_token / max_box_value, end_token / max_box_value]
```

After fusion, turn each box back into an inclusive token range and map the numeric label back to its string class. This is the pattern used by Feedback Prize style ensembling.

## 5. Suggested shape checks before calling the API

- Every model list should have the same number of boxes, scores, and labels.
- Every fused interval should be in normalized `[0, 1]` coordinates.
- Each `labels_list` entry should already be numeric.
- Every low-confidence candidate that should be ignored must fall below `skip_box_thr` before fusion.
