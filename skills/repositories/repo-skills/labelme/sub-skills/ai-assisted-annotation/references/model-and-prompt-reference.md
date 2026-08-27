# Model and Prompt Reference

## AI Assist models

| Model id | Display name | Point prompts | Box prompts |
| --- | --- | --- | --- |
| `efficientsam:10m` | EfficientSam (speed) | yes | yes |
| `efficientsam:latest` | EfficientSam (accuracy) | yes | yes |
| `sam:100m` | Sam (speed) | yes | yes |
| `sam:300m` | Sam (balanced) | yes | yes |
| `sam:latest` | Sam (accuracy) | yes | yes |
| `sam2:small` | Sam2 (speed) | yes | yes |
| `sam2:latest` | Sam2 (balanced) | yes | yes |
| `sam2:large` | Sam2 (accuracy) | yes | yes |
| `sam3:latest` | Sam3 | no | yes |

`sam3:latest` point prompts are rejected before session creation. Do not present
that as a model inference failure.

## AI Text Prompt models

| Model id | Display name | Prompt |
| --- | --- | --- |
| `yoloworld:latest` | YOLO-World (fast) | text list |
| `sam3:latest` | SAM3 (smart) | text list |

Text prompts are comma-separated in the widget (`dog,cat,bird`). The model
returns boxes, scores, labels, and optionally masks.

## Output formats

AI Assist output formats are:

- `polygon`
- `mask`
- `rectangle`
- `oriented_rectangle`
- `circle`

Polygon and mask output requires masks in the response. Rectangle output needs a
bounding box. Circle and oriented rectangle use a mask when available and fall
back to bbox-derived geometry when valid.

## Session behavior

- The OSAM session loads a model lazily.
- Image embeddings are cached by `image_id` with insertion-order eviction.
- If a model does not support image embedding, generation falls back to no
  embedding.
- Text prompts use request thresholds `iou_threshold=1.0`,
  `score_threshold=0.01`, and `max_annotations=1000` at the session layer;
  the GUI applies user-visible score and IoU filtering downstream.

## Existing Shape Suppression

Suppression compares detections to existing Shapes using IoU plus containment.
Containment catches nested masks where IoU alone is too low. When a candidate
matches an existing Shape, labelme highlights the existing Shape instead of
creating a duplicate if suppression is enabled.
