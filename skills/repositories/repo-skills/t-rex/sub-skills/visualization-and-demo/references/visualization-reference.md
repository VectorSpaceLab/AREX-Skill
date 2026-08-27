# T-Rex2 Visualization Reference

Use this reference when the task is to draw, threshold, or validate an existing T-Rex2 detection result. Use [../scripts/render_detections.py](../scripts/render_detections.py) for a reusable command-line renderer.

## Detection target schema

`trex.visualize(image_pil, target, ...)` expects `target` to contain three parallel arrays:

```json
{
  "scores": [0.97, 0.83],
  "labels": [1, 1],
  "boxes": [[12, 34, 56, 78], [90, 12, 140, 80]]
}
```

Rules:

- `boxes` must be `N x 4` pixel coordinates in `[x1, y1, x2, y2]` order.
- `scores`, `labels`, and `boxes` must have equal length.
- `scores` should be NumPy arrays, torch tensors, or scalar objects with `.item()` after iteration. Plain Python floats fail because the repo renderer calls `score.item()`.
- `labels` are rendered as text unless `draw_label=False` or the bundled CLI is called with `--no-draw-label`.
- Boxes are not normalized; do not pass `[cx, cy, w, h]` or 0-1 coordinates unless you convert them first.

## Verified renderer signature

```python
visualize(
    image_pil,
    target,
    return_point=False,
    draw_width=6.0,
    random_color=True,
    overwrite_color=None,
    agnostic_random_color=False,
    draw_score=False,
    draw_label=True,
)
```

Important options:

| Option | Effect | Notes |
|---|---|---|
| `return_point=True` | Draws the box center point instead of the rectangle. | Label text is not drawn in point mode. |
| `draw_width` | Rectangle outline width or point radius. | Converted to `int` for rectangles. |
| `random_color=True` | Picks a random color per label. | Non-deterministic colors are normal. |
| `overwrite_color={"1": (255, 0, 0)}` | Uses explicit colors by string label. | Provide every label after thresholding or rendering can fail. |
| `agnostic_random_color=True` | Uses a fresh random color per box. | Ignores label grouping. |
| `draw_score=True` | Draws `label score` text. | Requires scores that support `.item()`. |
| `draw_label=False` | Suppresses label text. | The bundled CLI exposes this as `--no-draw-label`. |

The function mutates and returns the same `PIL.Image` object. Open a copy if the original image must remain unchanged.

## Filtering recipe

Use a threshold only for display unless the user explicitly wants to remove low-confidence detections from downstream JSON.

```python
import numpy as np
from PIL import Image
from trex import visualize

raw = {"scores": [0.97, 0.12], "labels": [1, 1], "boxes": [[12, 34, 56, 78], [1, 2, 3, 4]]}
scores = np.asarray(raw["scores"], dtype=float)
labels = np.asarray(raw["labels"])
boxes = np.asarray(raw["boxes"], dtype=float)
mask = scores > 0.3
render_target = {"scores": scores[mask], "labels": labels[mask], "boxes": boxes[mask]}

image = Image.open("target.jpg").convert("RGB")
visualize(image, render_target, draw_score=True).save("annotated.jpg")
```

The bundled `render_detections.py` implements this pattern and also accepts output JSON from the cloud API scripts where detections are nested under a `detections` key.

## JSON formats accepted by the bundled renderer

Raw postprocess output:

```json
{"scores": [0.97], "labels": [1], "boxes": [[12, 34, 56, 78]]}
```

Cloud-script output:

```json
{
  "schema_version": 1,
  "workflow": "visual_prompt_inference",
  "detections": {
    "scores": [0.97],
    "labels": [1],
    "boxes": [[12, 34, 56, 78]]
  }
}
```

The renderer validates shape and length, filters by `--box-threshold`, converts scores to NumPy arrays, and writes an annotated image.

## Color control

Pass `--overwrite-colors-json` with a file such as:

```json
{
  "1": [255, 0, 0],
  "2": [0, 128, 255]
}
```

Keys are label strings. Values are RGB integer lists in `[0, 255]`. Include all labels that remain after thresholding.

## Output expectations

- The output image is a regular image file supported by Pillow based on the output extension.
- Empty detections are valid; the output image is saved unchanged.
- The renderer does not call the T-Rex2 cloud API and does not require a token.
- Rendering does not prove detection quality; it only proves that the result schema can be displayed.
