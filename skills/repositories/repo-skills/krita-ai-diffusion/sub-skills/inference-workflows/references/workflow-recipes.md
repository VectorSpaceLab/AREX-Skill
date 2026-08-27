# Workflow Recipes

Use these recipes to reason about request construction without running actual
image generation.

## Text-to-image generation

Expected request shape:

- `WorkflowKind.generate`
- `ImageInput.from_extent(canvas_extent)` with no `initial_image` for pure
  generation.
- `CheckpointInput` selected from the active style and server/client model list.
- `SamplingInput` from sampler preset and style CFG/steps.
- `ConditioningInput.positive` from root region prompt after comments,
  wildcards, layer tokens, style prompt, and LoRA tags are processed.

Useful checks:

```bash
python sub-skills/inference-workflows/scripts/inspect_workflow_input.py --kind generate --extent 512x512 --round-trip
```

## Refine / image-to-image

Expected request shape:

- `WorkflowKind.refine`
- `images.initial_image` contains canvas/image content.
- `SamplingInput.start_step` is set by strength; `actual_steps / total_steps`
  is the denoise strength.
- `conditioning.edit_reference` may be true for edit-model flows.

If a request unexpectedly becomes refine, inspect workspace `strength`; values
below 1.0 make the job use existing image content.

## Selection inpaint

Expected request shape:

- `WorkflowKind.inpaint`
- `images.initial_image` and `images.hires_mask` both present.
- `inpaint.target_bounds` identifies the affected bounds.
- `inpaint.fill`, `grow`, `feather`, `blend`, `use_inpaint_model`,
  `use_condition_mask`, and `use_reference` reflect the selected inpaint mode,
  architecture, prompt/control state, and strength.

`workflow.detect_inpaint_mode(extent, area)` returns `expand` if the selected
area reaches an image edge; otherwise it returns `fill`. `workflow.detect_inpaint`
then chooses fill/reference details. Test-backed examples include:

- `fill` on SD 1.5 with no prompt uses blur fill, inpaint model, and reference.
- `add_object` with a prompt can use the condition mask; adding control images
  disables condition-mask use.
- `replace_background` on SDXL uses replace fill and inpaint model without
  reference.
- Edit-reference prompts can force `FillMode.none` for fill mode.

Useful check:

```bash
python sub-skills/inference-workflows/scripts/inspect_workflow_input.py --kind inpaint --extent 512x512 --target-bounds 128,96,192,160 --round-trip
```

## Upscaling

Simple upscale:

- `WorkflowKind.upscale_simple`
- `UpscaleInput.model` names an upscaler.
- Fixed cost heuristic of 2.

Diffusion tiled upscale:

- `WorkflowKind.upscale_tiled`
- `images.extent.target` is the output resolution.
- `images.extent.desired` drives tile sizing; `passes_count` is twice the tile
  count, at least 2.
- `UpscaleInput.tile_overlap` can be auto/default (`-1`) or explicit.

Useful check:

```bash
python sub-skills/inference-workflows/scripts/inspect_workflow_input.py --kind upscale-tiled --extent 512x512 --target 2048x1536 --round-trip
```

## Control image and control layers

Control behavior crosses three objects:

1. `ControlInput` in `ConditioningInput.control` or region-specific controls.
2. `ControlMode` from the resource catalog, e.g. `line_art`, `depth`, `pose`,
   `scribble`, `reference`, or `inpaint`.
3. Client model resources for that architecture/control combination.

If control loading fails, do not only inspect the prompt. Also check server
resource discovery with the `server-resources` sub-skill. Some architectures use
ETN control nodes rather than a plain `ControlNetLoader`.

## Prompt, style, LoRA, wildcard, and layer preparation

`workflow.prepare_prompts` combines user prompt, negative prompt, style prompt,
style LoRAs, LoRA tags, wildcard choices, language/translation metadata, and
region prompts before `workflow.prepare` builds the final `WorkflowInput`.

Important behaviors:

- Prompt comments after `#` are stripped before final conditioning.
- Style prompts may contain `{prompt}` and are merged around the user prompt.
- Negative prompts can also use `{prompt}`.
- Wildcards such as `{apple|banana}` are evaluated with the job seed.
- `<lora:name:weight>` tags are removed from the text prompt and converted to
  `LoraInput`; missing explicit weights can use file metadata.
- Style-defined LoRAs are added to the final checkpoint input.
- `<layer:name>` tokens are replaced by image references after document/layer
  collection; this crosses into `document-image-state`.

Use the document-image helper for prompt/style diagnosis:

```bash
python sub-skills/document-image-state/scripts/inspect_prompt_style.py --prompt "cat <lora:fur:0.6> # note" --style-prompt "cinematic {prompt}" --lora-id fur --metadata
```

## ComfyUI lowering

`workflow.prepare(kind, ...)` builds `WorkflowInput`; `backend.workflow` then
lowers it into a `ComfyWorkflow` graph using helpers in `backend.comfy_workflow`.
The lowering layer is responsible for:

- Loading checkpoint/diffusion/text encoder/VAE models for the selected `Arch`.
- Applying LoRAs, clip skip, v-prediction/Zsnr, CFG rescale, attention guidance,
  dynamic caching, and tiled VAE flags.
- Encoding/decoding images and masks, region attention, control layers, inpaint
  references, high-resolution refinement, and tile extraction/merge.
- Using ETN nodes for image cache/load/save, translation, NSFW filtering,
  region masks, and control helpers.

When debugging generated graph shape, inspect payload fields first. Then inspect
model/resource availability and architecture compatibility with `server-resources`.

## Native evidence anchors

- `tests/test_workflow.py::test_inpaint_params` anchors inpaint mode behavior.
- `tests/test_workflow.py::test_prepare_lora`, `test_prepare_negative`, and
  `test_prepare_wildcards` anchor prompt/style/LoRA/wildcard behavior.
- `tests/test_model.py::test_generate_simple`, `test_generate_refine`, and
  `test_generate_inpaint` anchor `DocumentModel.generate()` request kind and
  image/mask payload behavior.
- `tests/test_comfy_workflow.py` anchors low-level graph helper behavior.
