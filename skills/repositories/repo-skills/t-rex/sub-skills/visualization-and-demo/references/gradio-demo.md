# Local Gradio Demo Reference

Use this when the user asks about the optional local UI for drawing T-Rex2 visual prompts. The Gradio demo is a convenience wrapper around the same cloud API covered by [../../cloud-api-workflows/SKILL.md](../../cloud-api-workflows/SKILL.md); live inference still needs a DeepDataSpace token and network access.

## What the demo provides

The UI exposes:

- A target image input.
- One interactive prompt image tab.
- Up to eight generic visual-prompt reference tabs.
- Threshold, point/box rendering, line width, and score display controls.
- Output image, count textbox, and a COCO-like annotation JSON textbox.

The UI chooses exactly one prompt mode per inference:

| User intent | Inputs to provide | Internal packer |
|---|---|---|
| Interactive visual prompt | Target image plus one prompted copy of that same target image. | `pack_model_input_interactive` |
| Generic visual prompt | Target image plus one or more prompted reference images. | `pack_model_input_generic` |

Supplying both an interactive prompt and generic prompts raises an error. Supplying neither also raises an error.

## Dependencies and launch boundary

The UI layer needs dependencies beyond the core cloud wrapper:

```bash
pip install gradio==4.44.1 gradio-image-prompter
```

A compatibility repair may be needed for older Gradio:

```bash
pip install 'huggingface_hub<1.0'
```

The demo also needs a valid API token for live inference. This generated skill does not bundle a full Gradio server because the original app is an optional, long-running UI with credentialed live API calls and checkout-specific assets. For self-contained or automated work, use the bundled cloud scripts and renderer instead. If the user explicitly provides a current T-Rex checkout and asks to operate that checkout's UI, inspect that checkout first and treat the server launch as a user-authorized service process rather than a bounded smoke check.

## Prompt parsing behavior

The demo's `parse_visual_prompt(points)` separates drawn objects into:

- Boxes when point entries indicate press-drag box prompts.
- Positive points when entries indicate positive point prompts.
- Negative points when entries indicate negative point prompts.

However, both interactive and generic packers reject point-only prompts in the repo code with an error message that says point prompts are not supported for now. In practice, use rectangle prompts for reliable UI behavior.

## Inference behavior

The UI calls `trex2.visual_prompt_inference(target_image, prompts)[0]` for both prompt modes, then filters detections by the visual threshold and draws boxes through an internal `plot_boxes_to_image` helper.

Postprocessing details:

- Scores, boxes, and labels are converted to NumPy arrays before filtering.
- The filtered box count is returned as a text output.
- A COCO-like annotation JSON is built from filtered boxes.
- The annotation builder expects boxes as NumPy arrays and converts `[x1, y1, x2, y2]` to `[x, y, width, height]` for each entry.

## When to prefer bundled scripts instead of the UI

Prefer [cloud API workflows](../../cloud-api-workflows/SKILL.md) and [render_detections.py](../scripts/render_detections.py) when:

- The task is automated or headless.
- The user already has prompt JSON coordinates.
- The user needs reproducible output files.
- The environment cannot launch a browser/server.
- The task is a bounded verification or smoke check.

Use the UI reference when the task is interactive annotation, manual prompt drawing, user demonstration, or debugging a Gradio-specific prompt issue.
