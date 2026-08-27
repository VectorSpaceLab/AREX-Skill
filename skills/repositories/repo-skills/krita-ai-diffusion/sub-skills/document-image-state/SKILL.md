---
name: document-image-state
description: "Guides Krita AI Diffusion document, layer, region, Image, Mask,
  Bounds, prompt, style, metadata, and persistence state tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# document-image-state

Use this sub-skill when the task is about Krita document/layer state, image and
mask helpers, prompt/style processing, LoRA tags, regions, persistence, or how
canvas data enters/leaves workflows.

Trigger examples:

- Converting between Krita pixel data and `ai_diffusion.image.Image`, `Mask`,
  `Bounds`, `Extent`, or `ImageCollection`.
- Debugging active selection, layer bounds, region masks, control layers, or
  apply behavior after generation.
- Understanding prompt comments, `{wildcards}`, `<lora:name:weight>`,
  `<layer:name>` tokens, style prompt merge, negative prompt merge, or PNG
  metadata.
- Working with `Style`, `Styles`, sampler presets, settings JSON, document
  persistence, or observable persisted properties.

## Safe entry point

```bash
python sub-skills/document-image-state/scripts/inspect_prompt_style.py --prompt "cat <lora:fur:0.6> # note" --style-prompt "cinematic {prompt}" --lora-id fur --metadata
```

The helper analyzes prompt/style behavior offline. It does not launch Krita,
connect to ComfyUI, read private images, download models, or run generation.

## References

- [references/document-layer-image-reference.md](references/document-layer-image-reference.md):
  document/layer/image/mask/bounds APIs and data flow.
- [references/prompt-style-persistence.md](references/prompt-style-persistence.md):
  prompt, style, LoRA, wildcard, metadata, and persistence behavior.
- [references/troubleshooting.md](references/troubleshooting.md): selection,
  layer, image, prompt, style, metadata, and persistence failure recovery.
- [scripts/inspect_prompt_style.py](scripts/inspect_prompt_style.py): bundled
  offline prompt/style inspector.

## Boundaries

- For final request dataclasses and workflow cost/pass behavior, route to
  `inference-workflows`.
- For UI controls and workspace state that decide when document data is
  collected, route to `ui-workspaces`.
- For custom graph placeholders that request layers/masks/canvas data, route to
  `custom-graphs` too.
