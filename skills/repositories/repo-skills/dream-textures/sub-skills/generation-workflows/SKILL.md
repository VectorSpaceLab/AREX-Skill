---
name: generation-workflows
description: "Operate Dream Textures prompt, image editing, ControlNet, history,
  seamless texture, and AI upscaling workflows in Blender."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Generation Workflows

Use this sub-skill when a task is about generating, modifying, repairing, extending, recalling, or upscaling images with Dream Textures from Blender's Dream panel, Image Editor, Shader Editor, prompt history, or selected Image Texture nodes.

## Route here

- Generate a texture or image from a prompt with `Generate`, prompt presets, negative prompts, scheduler/steps/CFG/seed, iterations, or file-batch prompt lines.
- Modify a source image with image-to-image strength/fit, generated depth, depth map, or depth-only conditioning.
- Make a texture seamless, interpret seamless axes, or understand auto-detection from source images and history hashes.
- Inpaint or repair an image using alpha masks, prompt masks, the Mark Inpaint Area brush, or seamless inpainting.
- Outpaint an image using tile size, top-left origin coordinates, overlap, and bounds checks.
- Add ControlNet models, control images, conditioning scales, and image processors/baked control images to a prompt.
- Export, import, validate, or edit prompt-history JSON.
- Upscale from the AI Upscaling panel using a selected Image Texture node or open Image Editor image, tile size, blend, prompt guidance, and seamless axes.

## Reroute

- Installing the add-on, dependency variants, Hugging Face/DreamStudio credentials, model download/import/linking, checkpoint config choices, and model cache failures: use `../setup-and-models/SKILL.md`.
- 3D texture projection, viewport depth/color inputs, render-pass/compositor workflows, and scene annotation maps: use `../scene-integration/SKILL.md`.
- Backend class internals, custom backend implementation, generator actor details, scheduler enum implementation, and Diffusers pipeline diagnosis: use `../backend-and-api/SKILL.md`.
- Full Stable Diffusion inference, model downloads, or Blender UI automation are outside this sub-skill's bundled scripts; use the scripts here only for safe planning and validation.

## Start fast

1. Open an Image Editor or Shader Editor, show the sidebar with `N`, select the `Dream` tab, choose `Backend` and `Model`, then configure the `Prompt`, `Size`, `Source Image`, `ControlNet`, and `Advanced` panels before pressing `Generate`.
2. Match the selected model type to the task: prompt-to-image/image-to-image use a prompt-to-image model; depth modes use a depth model; inpaint/outpaint use an inpainting model; upscaling uses the Stable Diffusion x4 upscaler model; ControlNet also needs compatible ControlNet model entries.
3. Use numeric seeds for repeatability. Random seed stores the actual result seed in history; text seeds are hashed by the running Blender/Python process and should be recalled from history rather than assumed stable across sessions.
4. Keep generation dimensions in 64-pixel increments for the UI workflow, and reduce size, steps, batch/iterations, preview accuracy, or tile size when VRAM errors appear.
5. For outpaint math, run the bundled planner before entering coordinates in Blender:

```bash
python scripts/plan_outpaint_origin.py --source-size 512x960 --tile-size 512x512 --overlap 64 --region bottom-right
```

6. Before importing or editing prompt-history JSON, validate it without Blender:

```bash
python scripts/validate_prompt_history_json.py path/to/prompt-history.json
```

## References

- `references/image-generation.md` maps Dream panel fields to generation arguments, prompt-to-image, source-image modify/depth modes, negative prompts, size/seed/scheduler/seamless/iterations, and ControlNet.
- `references/editing-and-upscaling.md` covers inpainting, seamless repair, outpainting origin/overlap math, and AI upscaling tile/blend behavior.
- `references/prompting-history-seamless.md` covers prompt presets, file-batch prompts, history export/import JSON, validation, and seamless auto-detection behavior.
- `references/troubleshooting.md` maps common Blender UI and parameter failures to recovery steps.

## Bundled safe scripts

- `scripts/plan_outpaint_origin.py` computes and validates Dream Textures outpaint origins from source size, tile size, overlap, region, and strategy. It never imports Blender or downloads models.
- `scripts/validate_prompt_history_json.py` validates Dream Textures prompt-history JSON keys, types, enums, and selected cross-field constraints. It never imports Blender or downloads models.
