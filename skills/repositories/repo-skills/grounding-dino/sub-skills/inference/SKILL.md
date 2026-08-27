---
name: inference
description: "Use GroundingDINO for single-image open-vocabulary detection,
  Python inference APIs, token spans, annotation, device selection, and output
  interpretation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# GroundingDINO Inference

Use this sub-skill when a user needs single-image GroundingDINO inference with text prompts, class lists, token spans, annotated output images, or Python API integration.

## Use This For

- Loading a GroundingDINO config/checkpoint and one image for open-vocabulary object detection.
- Choosing between `groundingdino.util.inference` functions and the `Model` wrapper API.
- Building prompts from free-form captions or class lists such as `cat . dog . person .`.
- Using token spans to target exact phrases inside a sentence prompt.
- Interpreting normalized `cxcywh` boxes, pixel `xyxy` annotations, logits/confidence, and phrases.
- Running the bundled CLI helper in `scripts/grounding_dino_infer.py` with explicit input validation.

## Route Elsewhere

- COCO AP and benchmark evaluation: use `../evaluation/`.
- Folder pseudo-label export or COCO-format dataset creation: use `../dataset-annotation/`.
- Gradio, Hugging Face demo, Grounded-SAM, GLIGEN, or image-editing pipelines: use `../integrations/`.
- Training or fine-tuning: treat as an unsupported gap because GroundingDINO training code is not released in this repo skill.

## Quick Start

Prefer the bundled helper for one-off runs because it validates config, checkpoint, image, token spans, thresholds, and device before loading the model:

```bash
python sub-skills/inference/scripts/grounding_dino_infer.py \
  --config-file /path/to/GroundingDINO_SwinT_OGC.py \
  --checkpoint-path /path/to/groundingdino_swint_ogc.pth \
  --image-path /path/to/image.jpg \
  --text-prompt "chair . person . dog ." \
  --output-dir outputs/grounding-dino \
  --box-threshold 0.35 \
  --text-threshold 0.25 \
  --device cuda \
  --json-output
```

For CPU-only checks, add `--cpu-only`. For class-list prompts, use `--classes cat dog "traffic light"` instead of `--text-prompt`. For span-targeted phrases, use `--text-prompt` plus `--token-spans`; see `references/token-spans.md`.

## References

- `references/api-reference.md`: function signatures, wrapper API, inputs, outputs, and box formats.
- `references/workflows.md`: CLI helper recipes, Python API recipes, validation commands, and output interpretation.
- `references/token-spans.md`: token span schema, offset validation, examples, and failure signals.
- `references/troubleshooting.md`: missing files, CPU/CUDA, `_C` custom op errors, no detections, and malformed prompts/spans.
