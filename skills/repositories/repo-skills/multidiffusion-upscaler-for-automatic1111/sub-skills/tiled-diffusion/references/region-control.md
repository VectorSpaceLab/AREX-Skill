# Regional Prompt Control

## Purpose

Use this reference when a task involves per-region prompts, negative prompts, seeds, foreground/background blending, bbox save/load, or the on-canvas region editor in the Tiled Diffusion panel.

## Region controls

The extension builds a fixed set of region controls. The number of regions is the WebUI command option `md_max_regions` capped at 16, defaulting to 8 when the option is not set.

Each region has this schema:

| Field | Meaning | Notes |
| --- | --- | --- |
| Enable Region | Whether this bbox participates. | Disabled boxes are ignored. |
| `x`, `y`, `w`, `h` | Normalized position and size from 0.0 to 1.0. | Values are rounded to 4 decimals and clamped to image/latent bounds. |
| Prompt | Prompt fragment appended to the base prompt for this region. | Styles and extra networks are parsed for the region prompt. |
| Negative Prompt | Negative prompt fragment appended for this region. | Used when reconstructing region unconditional conditioning. |
| Type | `Background` or `Foreground`. | Background contributes to the normal tiled canvas; foreground is feather-blended over it. |
| Feather | Foreground feather ratio from 0 to 1. | Visible only for foreground regions. |
| Seed | Region seed. | `-1` means random/fixed by WebUI; the UI can reuse a seed from PNG info. |

## Background vs foreground

- **Background** regions add their generated tile output to the main tiled buffer.
- **Foreground** regions create a separate feather mask and blend foreground output over the current background.
- If **Draw full canvas background** is disabled, only enabled custom boxes are drawn and the grid background is skipped.

Use foreground when a region should be blended on top of the base image. Use background when the region should replace or participate in the normal background sampling.

## Canvas editor behavior

The browser-side helper draws colored bbox overlays on a reference image for txt2img or img2img.

- For txt2img, **Create txt2img canvas** creates a white reference image using either overwrite-size controls or the current txt2img size.
- For img2img, **From img2img** uses the current input image.
- Dragging/resizing a box updates `x`, `y`, `w`, and `h` sliders.
- A region-size warning appears when a bbox is very large relative to a 1280-pixel threshold and img2img upscale factor; large regions can increase VRAM use.
- For older Gradio 3.17-3.28 accordion behavior, the helper rerenders boxes when accordions reopen. If boxes disappear or become stale, updating WebUI/Gradio or reopening the panel can help.

## Save/load config behavior

The panel exposes **Custom Config File**, **Save**, and **Load** controls. The default file name is `config.json`.

The saved JSON shape is:

```json
{
  "bbox_controls": [
    {
      "enable": true,
      "x": 0.4,
      "y": 0.4,
      "w": 0.2,
      "h": 0.2,
      "prompt": "region prompt fragment",
      "neg_prompt": "region negative fragment",
      "blend_mode": "Background",
      "feather_ratio": 0.2,
      "seed": -1
    }
  ]
}
```

Operational notes:

- Config files are stored in the extension's runtime `region_configs/` directory, not inside this skill.
- Loading requires a reference image to exist first; otherwise the UI reports that the user must create or upload a ref image.
- Missing files and malformed JSON return visible red HTML error messages in the panel.
- Missing fields in a loaded bbox become `None`; unspecified unused boxes fall back to default disabled settings.

## Region prompt troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Box controls do nothing | Region is disabled, no reference image exists, or accordion DOM was not rendered. | Enable the region, create a canvas/ref image, reopen the accordion, then move a slider. |
| Region output ignores the prompt | Region was too small after normalization/clamping, region disabled, or Draw Background/Foreground semantics were misunderstood. | Check normalized box dimensions and blend mode. |
| Seed reuse button keeps current seed | PNG info has no `Region control` data or selected region id is absent. | Run a generation with region control enabled first, then reuse seed. |
| Save/load fails | Empty config name, missing file, or invalid JSON. | Use a simple file name such as `config.json`, save once, then load after a ref image exists. |
| VRAM spikes with region control | Large foreground/background boxes and ControlNet tensors multiply tile work. | Shrink boxes, reduce tile batch size, or enable ControlNet tensor CPU transfer. |
