---
name: utilities
description: "Guides Autodistill image loading, visualization, model comparison,
  video splitting, and Roboflow utility boundaries."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Autodistill Utilities

Use this sub-skill when a task asks about image loading/conversion, plotting detections, comparing model predictions, splitting video frames, understanding `split_data` side effects, or Roboflow synchronization helper boundaries.

For main auto-labeling workflows and dataset layout, use [dataset labeling](../dataset-labeling/SKILL.md). For CLI model selection, use [CLI and model registry](../cli-and-model-registry/SKILL.md). For custom model interface design, use [ontologies and model interfaces](../ontologies-and-model-interfaces/SKILL.md).

## Quick Route

- **Image input conversion:** read [image loading and visualization](references/image-loading-and-visualization.md) for `load_image` accepted inputs/outputs and headless plotting guidance.
- **Utility function signatures and side effects:** read [utility reference](references/utility-reference.md) for `load_image`, `split_data`, `split_video_frames`, `sync_with_roboflow`, `plot`, and `compare`.
- **Utility failures:** read [troubleshooting](references/troubleshooting.md) for invalid paths, unsupported return formats, URL/network failures, OpenCV/Pillow issues, headless display, Roboflow credentials, and directory mutation.
- **Safe local image-loading check:** run [scripts/check_image_loading.py](scripts/check_image_loading.py). It creates its own local fixture by default and does not need network.

## Common Pattern

```python
from autodistill.helpers import load_image

cv2_image = load_image("image.jpg", return_format="cv2")
pil_image = load_image(cv2_image, return_format="PIL")
np_image = load_image(pil_image, return_format="numpy")
```

Use `load_image` when a plugin expects a specific image object format but your workflow has a path, PIL image, or NumPy/OpenCV array.

## Headless Visualization Pattern

```python
from autodistill.utils import plot

annotated = plot(image=image, detections=detections, classes=classes, raw=True)
# Save or inspect annotated instead of relying on an interactive display.
```

`plot(..., raw=False)` uses `supervision.plot_image`, which may not be suitable for headless runs.

## Safety Notes

- `load_image` can fetch HTTP URLs; avoid that branch unless network use is approved.
- `sync_with_roboflow` logs into Roboflow, downloads images, labels them, and uploads annotations; treat it as credentialed and externally mutating.
- `split_data` mutates a dataset output directory by moving files and converting `.png`/`.jpeg` to `.jpg` inside that output layout.
