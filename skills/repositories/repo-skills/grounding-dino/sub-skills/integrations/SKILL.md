---
name: integrations
description: "Build safe GroundingDINO web demos and handoffs to segmentation,
  Grounded-SAM, Stable Diffusion, GLIGEN, or notebook-style integrations without
  running unsafe source demo side effects."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# GroundingDINO Integrations

Use this sub-skill when a task asks to embed GroundingDINO detections in a web app, Hugging Face checkpoint loading flow, Gradio demo, Grounded-SAM or segmentation handoff, image-editing pipeline, or external notebook ecosystem.

## Route First

- For single-image CLI/API inference, model loading, `predict`, `annotate`, token spans, and threshold tuning, use `../inference/`.
- For pseudo-labeling image folders or exporting COCO-style annotations, use `../dataset-annotation/`.
- For COCO AP or benchmark evaluation, use `../evaluation/`.
- For Gradio UI, Hugging Face checkpoint download UX, downstream RGB/BGR or box-format handoff, and notebook integration caveats, stay here.

## Integration Patterns

- Local web demo: use `scripts/grounding_dino_gradio_app.py` rather than source demos that mutate environments at import/run time.
- Hugging Face checkpoint loading: use `--hf-repo-id` and `--hf-filename` only when the user explicitly wants a download; otherwise pass an already-downloaded `--checkpoint`.
- Gradio inputs: accept uploaded images as PIL, convert to RGB, run GroundingDINO on transformed tensors, and return a PIL RGB annotated image.
- Segmentation/editing handoff: pass image data, detected phrases, confidence scores, and boxes with an explicit color-space and coordinate contract.
- External notebooks: treat Stable Diffusion, GLIGEN, SAM, and Grounded-SAM integrations as separate model stacks with their own environment, checkpoint, network, GPU, and license requirements.

## References

- [Web demo workflow](references/web-demo.md) for safe Gradio app structure, CLI options, validation checks, and launch examples.
- [Image-editing integrations](references/image-editing-integrations.md) for SAM/Grounded-SAM, Stable Diffusion, GLIGEN, RGB/BGR, and box-format handoffs.
- [Troubleshooting](references/troubleshooting.md) for dependency, network, device, latency, color-space, and unsafe source-demo issues.

## Bundled Script

```bash
python sub-skills/integrations/scripts/grounding_dino_gradio_app.py --help
```

The wrapper never runs `pip install`, `setup.py`, or source checkout scripts. It imports `gradio` and `huggingface_hub` only when needed after argument parsing, validates local config/checkpoint paths, and downloads weights only when both `--hf-repo-id` and `--hf-filename` are provided.
