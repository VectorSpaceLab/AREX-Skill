---
name: prompted-segmentation
description: "Use SAM's SamPredictor for prompt-based masks from points, labels,
  boxes, iterative low-res mask refinement, image embeddings, and CPU/GPU
  checkpoint setup."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Prompted Segmentation

Use this sub-skill when the user wants Segment Anything (SAM) masks for a specific object or region using prompts such as foreground/background points, boxes, prior masks, or repeated prompts on the same image.

## When to Use

- Segment an object from a point prompt, box prompt, or combined box plus foreground/background points.
- Reuse one image embedding for multiple prompt attempts with `SamPredictor.set_image(...)` followed by repeated `predict(...)` calls.
- Refine a mask interactively by passing the best previous `low_res_masks` slice back as `mask_input`.
- Debug prompt shape, image format, checkpoint, model type, or device mismatch failures.
- Extract image embeddings for an ONNX/browser handoff with `get_image_embedding()`; route ONNX export and browser runtime work to `../onnx-and-browser/`.

For full-image proposal generation without prompts, use `../automatic-mask-generation/` instead.

## Core Pattern

1. Choose a model type from `default`, `vit_h`, `vit_l`, or `vit_b`, and pass the matching user-provided checkpoint path to `sam_model_registry[model_type](checkpoint=...)`.
2. Move the SAM model to the selected device before creating or using the predictor: `sam.to(device=device)`.
3. Create `predictor = SamPredictor(sam)` and call `predictor.set_image(image, image_format="RGB")` once per image.
4. Pass prompts in original image pixel coordinates: points as `Nx2` `(x, y)`, point labels as length `N` with `1` foreground and `0` background, and boxes as `XYXY`.
5. Use `multimask_output=True` for ambiguous single-click prompts; use `False` for boxes or multiple prompts when one mask is desired.
6. Read outputs as `(masks, scores, low_res_masks)`, where `masks` is `CxHxW`, `scores` is length `C`, and `low_res_masks` is `Cx256x256` logits for refinement.

## Required Details

- API signatures, return shapes, and direct `Sam` batch notes: `references/api-reference.md`.
- Prompting workflows, embedding reuse, and iterative refinement: `references/workflows.md`.
- Diagnosis for common runtime failures and shape errors: `references/troubleshooting.md`.
- Safe command-line helper template: `scripts/predictor_prompt_template.py`.

## Minimal Prompt Example

```python
import numpy as np
import torch
from segment_anything import SamPredictor, sam_model_registry

model_type = "vit_b"
device = "cuda" if torch.cuda.is_available() else "cpu"
sam = sam_model_registry[model_type](checkpoint="/path/to/sam_vit_b.pth")
sam.to(device=device)
predictor = SamPredictor(sam)
predictor.set_image(image_rgb_uint8_hwc, image_format="RGB")

point_coords = np.array([[500, 375]], dtype=np.float32)
point_labels = np.array([1], dtype=np.int32)
masks, scores, low_res_masks = predictor.predict(
    point_coords=point_coords,
    point_labels=point_labels,
    multimask_output=True,
)
best_mask = masks[int(np.argmax(scores))]
```
