# Visualization and Demo Troubleshooting

Use this for rendering, detection JSON, and Gradio UI failures. Route live API and token failures to [../../cloud-api-workflows/references/troubleshooting.md](../../cloud-api-workflows/references/troubleshooting.md). Route package installation failures to the root troubleshooting reference.

## Rendering failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `AttributeError: 'float' object has no attribute 'item'` | `trex.visualize` iterates scores and calls `.item()`; plain Python floats do not satisfy that contract. | Use `render_detections.py`, or convert `scores` to a NumPy array/torch tensor before calling `visualize`. |
| `KeyError: 'boxes'`, `KeyError: 'scores'`, or `KeyError: 'labels'` | Detection JSON does not contain the required target keys, or the detections are nested under an unexpected key. | Use raw `{"scores", "labels", "boxes"}` JSON or cloud-script JSON with a `detections` object. |
| Shape error for boxes | Boxes are missing values, are not `N x 4`, or use another format such as `[cx, cy, w, h]`. | Convert to pixel `[x1, y1, x2, y2]` before rendering. |
| Scores/labels/boxes length mismatch | The arrays were filtered separately or copied from different results. | Filter with one mask derived from scores and apply it to all arrays together. |
| Color lookup failure with `overwrite_color` | Explicit color mapping does not include every label after filtering. | Add all label keys as strings or remove the overwrite color mapping. |
| Output image is unchanged | All detections were filtered out by `--box-threshold`, or the detections list is empty. | Lower the threshold or inspect the input JSON summary. Empty detections are valid and save the original image. |
| Text labels are unreadable or too large | `draw_width`, score labels, or colors are not suitable for the image size. | Use `--draw-width`, `--no-draw-label`, or explicit colors. |

## Gradio demo failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ImportError: cannot import name 'HfFolder' from 'huggingface_hub'` | `gradio==4.44.1` expects an older `huggingface_hub` API. | Install a compatible version such as `huggingface_hub<1.0` in the demo environment. |
| `ModuleNotFoundError: gradio_image_prompter` | The optional UI helper is missing. | Install `gradio-image-prompter` before launching the UI. |
| Error says point prompts are not supported | The repo packers reject point-only prompt inputs even though the UI labels mention point prompts. | Draw rectangle/box prompts instead. |
| Error says to provide either interactive or generic visual prompt | The UI received both prompt modes or neither. | For interactive mode, supply only the target-image prompt tab. For generic mode, leave interactive empty and fill one or more generic tabs. |
| `Please provide a target image` | Target image input is empty. | Provide a target image before pressing run. |
| UI launches but inference fails | The UI still calls the DeepDataSpace API and needs a valid token, network access, and quota. | Validate the same prompt through the cloud sub-skill in dry-run mode, then retry with a valid token. |
| Server blocks a terminal or smoke test | Launching Gradio is a long-running service process. | Do not use full launch as a bounded verification. Use `--help`/import checks or the bundled scripts for automated tasks. |

## Safe recovery pattern for renderer calls

```python
import numpy as np
from trex import visualize

result = {"scores": [0.9], "labels": [1], "boxes": [[1, 2, 20, 22]]}
target = {
    "scores": np.asarray(result["scores"], dtype=float),
    "labels": np.asarray(result["labels"]),
    "boxes": np.asarray(result["boxes"], dtype=float),
}
visualize(image, target, draw_score=True)
```

Prefer the bundled renderer for file-based workflows because it performs these conversions and validations automatically.
