# 3D WBF troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Boxes fuse in the wrong place or shape | The box order is not `[x1, y1, z1, x2, y2, z2]`, or the axes were permuted | Reorder the coordinates so each box follows x/y/z corner pairs. Keep the axis meaning unchanged. |
| Warnings say coordinates are `< 0` or `> 1` | The inputs are still in metric units or another unnormalized range | Normalize each axis to a common `[0, 1]` scene or volume first, then fuse. |
| `x2 < x1`, `y2 < y1`, or `z2 < z1` appears in a warning | The corners were reversed on one or more axes | Sort each axis pair before fusion. The implementation swaps reversed corners, but it is better to clean the inputs first. |
| The fused result disappears or a box is skipped | The box has zero volume after clipping or the corners are identical | Ensure each axis span is positive. Check for degenerate boxes before calling WBF. |
| The function prints `Error. Unknown conf_type ... Use "avg"` | A 3D-only unsupported mode such as `absent_model_aware_avg` was requested | Use `conf_type='avg'` or `conf_type='max'`. If the string is invalid, the implementation falls back to `avg`. |
| Confidence values do not match expectations | The wrong aggregation mode or weight settings were chosen | Compare `avg` and `max` on a tiny test case. Keep weights aligned with the model order. |
| A warning says the number of weights is incorrect | The `weights` list does not match the number of models | Provide exactly one weight per model, or omit `weights` to use ones. |
| The function exits on length mismatch | One of the box, score, or label lists has a different length | Make sure each model has matching numbers of boxes, scores, and labels. |
| The user expects GPU acceleration | This API does not need a GPU backend | Use the CPU environment. NumPy/Numba is enough for 3D fusion. |
| Matplotlib or OpenCV are missing | Visualization extras are optional, not required for fusion | Skip plotting for runtime skill use. The fusion API itself does not depend on GUI libraries. |
| Labels look like floats in the output | NumPy arrays may store numeric labels as float values | Cast labels back to integer ids when you need class ids downstream. |

## Fast checks

- Confirm the six-coordinate order first.
- Confirm all coordinates are normalized to `[0, 1]`.
- Confirm the task really wants 3D WBF and not a 2D or 1D workflow.
- Confirm the confidence mode is one of `avg` or `max`.
- Confirm you are not asking the skill to do visualization or coordinate conversion work it does not own.
