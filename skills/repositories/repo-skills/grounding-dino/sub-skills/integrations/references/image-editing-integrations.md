# Image Editing And Segmentation Integrations

GroundingDINO supplies open-vocabulary boxes and phrases. Segmentation, inpainting, GLIGEN, Stable Diffusion, SAM, and Grounded-SAM workflows are downstream consumers with separate dependencies and runtime risks. Keep the GroundingDINO stage small, explicit, and testable; hand off only well-defined image, box, phrase, and score data.

## What GroundingDINO Produces

The core `predict` API returns:

| Value | Shape/type | Coordinate contract | Common downstream use |
| --- | --- | --- | --- |
| `boxes` | `torch.Tensor[N, 4]` | Normalized `cxcywh` in `[0, 1]` relative to image width/height | Convert before masks, SAM prompts, GLIGEN boxes, or annotation export. |
| `logits` | `torch.Tensor[N]` | Detection confidence per retained box | Filter or display confidence. |
| `phrases` | `list[str]` | Text phrase linked to each box | Object label, SAM prompt metadata, GLIGEN phrase list, UI display. |
| `image_source` | `np.ndarray[H, W, 3]` | RGB when produced by `load_image` | Convert to PIL RGB for diffusion/inpainting; convert to BGR only for OpenCV drawing. |

`annotate(image_source, boxes, logits, phrases)` draws with OpenCV conventions and returns a BGR ndarray. Convert it back to RGB before passing to PIL, Gradio, notebooks, or web clients.

## Box Conversion Recipes

Pixel `xyxy` boxes for SAM-like segmentation, mask creation, or annotation libraries:

```python
import torch
from torchvision.ops import box_convert

height, width = image_source.shape[:2]
boxes_pixel_cxcywh = boxes * torch.tensor([width, height, width, height])
boxes_pixel_xyxy = box_convert(boxes_pixel_cxcywh, in_fmt="cxcywh", out_fmt="xyxy")
```

Normalized `xyxy` boxes for GLIGEN-style prompt boxes:

```python
from torchvision.ops import box_convert

gligen_boxes = box_convert(boxes=boxes, in_fmt="cxcywh", out_fmt="xyxy").tolist()
```

Rectangular inpainting mask from GroundingDINO boxes:

```python
import numpy as np

mask = np.zeros_like(image_source, dtype=np.uint8)
for x0, y0, x1, y1 in boxes_pixel_xyxy.cpu().numpy():
    x0, y0 = max(int(x0), 0), max(int(y0), 0)
    x1, y1 = min(int(x1), width), min(int(y1), height)
    mask[y0:y1, x0:x1, :] = 255
```

For diffusion inpainting, white mask pixels usually mark the area to edit and black pixels mark the area to keep. Confirm the downstream pipeline's convention before running.

## Color-Space Handoffs

| Component | Expected color format | Action |
| --- | --- | --- |
| `load_image` output | RGB ndarray | Safe for PIL and web display. |
| OpenCV `cv2.imread` | BGR ndarray | Convert to RGB before PIL/diffusion; `Model.preprocess_image` expects BGR for that wrapper path. |
| `annotate` output | BGR ndarray | Convert with `cv2.cvtColor(output, cv2.COLOR_BGR2RGB)` before PIL/Gradio. |
| PIL / Gradio image | RGB | Use `.convert("RGB")` before GroundingDINO transforms. |
| Stable Diffusion inpainting | PIL RGB image and PIL mask | Resize image and mask together to the pipeline resolution. |
| GLIGEN inpainting | PIL RGB image plus normalized `xyxy` boxes and phrases | Keep `gligen_phrases` length aligned with `gligen_boxes`. |

## Grounded-SAM Or SAM Handoff

GroundingDINO can act as the text-conditioned box proposal stage for segmentation.

1. Run GroundingDINO with a prompt such as `cat . dog .` and conservative thresholds.
2. Convert normalized `cxcywh` boxes to pixel `xyxy` boxes in the original image coordinate system.
3. Pass pixel `xyxy` boxes to the segmentation model's box-prompt API.
4. Preserve `phrases` and `logits` alongside masks so downstream consumers know which object each mask represents.
5. Keep the SAM or Grounded-SAM install separate from the GroundingDINO base environment unless the user explicitly wants a combined environment.

Segmentation stacks often bring their own checkpoint downloads, GPU kernels, image resizing policies, and output mask conventions. Validate one image end-to-end before batching.

## Stable Diffusion Inpainting Pattern

The notebook workflow used GroundingDINO to locate an object, built a rectangular mask from detected boxes, resized image and mask to the diffusion pipeline resolution, and passed both to a Stable Diffusion inpainting pipeline. Recreate that pattern only after the user accepts the external stack requirements.

Checklist:

- Run GroundingDINO first and inspect boxes/masks before invoking diffusion.
- Convert the original image to PIL RGB and the mask to PIL before inpainting.
- Resize image and mask together, commonly to `512 x 512` for older inpainting checkpoints.
- Confirm white-mask-means-edit semantics for the selected pipeline.
- Keep prompts separate: the detection prompt finds boxes; the generation prompt describes the desired edit.
- Expect GPU memory pressure and large model downloads outside GroundingDINO's requirements.

## GLIGEN Pattern

The GLIGEN notebook used GroundingDINO boxes as grounding boxes for a GLIGEN inpainting pipeline and supplied a phrase per box.

Checklist:

- Convert GroundingDINO normalized `cxcywh` boxes to normalized `xyxy` for GLIGEN-like APIs.
- Keep `len(gligen_phrases) == len(gligen_boxes)` after filtering detections.
- Use phrases appropriate for generation, not necessarily the raw detection labels.
- GLIGEN examples may require modified `diffusers`, pinned versions, or a dedicated environment.
- Treat GLIGEN setup and model downloads as external to this GroundingDINO skill.

## Notebook Ecosystem Boundaries

The repository notebooks are reference-only integration evidence. Do not make runtime skills depend on them because they assume notebook execution, network downloads, external repositories, separate environments, and GPU-oriented model stacks. A safer production integration decomposes the work into explicit stages:

1. GroundingDINO detection: config, checkpoint, prompt, thresholds, RGB image, normalized boxes.
2. Handoff validation: expected number of boxes, phrase alignment, coordinate conversion, color-space conversion.
3. External model stage: SAM, Stable Diffusion, GLIGEN, or another editor in its own environment.
4. Result validation: masks align with objects, edits affect intended regions, no BGR/RGB color inversion, and memory/network failures are handled.
