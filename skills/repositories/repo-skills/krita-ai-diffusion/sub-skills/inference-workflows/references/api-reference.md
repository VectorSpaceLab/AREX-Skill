# Workflow API Reference

This reference summarizes the public request objects used by Krita AI Diffusion
to describe a generation job. The contract lives in `ai_diffusion.backend.api`.
Everything relevant to image generation should be represented in
`WorkflowInput` before a local ComfyUI or cloud client receives the request.

## `WorkflowKind`

| Kind | Typical trigger | Required/important fields |
| --- | --- | --- |
| `generate` | Text-to-image or canvas generation with no input image requirement | `images.extent`, `models`, `sampling`, `conditioning`; `images.initial_image` usually `None`. |
| `refine` | Strength below 1.0 or edit/refine existing canvas/image | `images.initial_image`, `models`, `sampling`, `conditioning`; denoise is derived from `sampling.start_step`. |
| `inpaint` | Active selection or inpaint tool | `images.initial_image`, `images.hires_mask`, `inpaint`, `conditioning`, `models`, `sampling`. |
| `refine_region` | Region-only refinement | Region/mask state in `conditioning.regions` and input image/mask extents. |
| `upscale_simple` | Upscale with an upscaler model only | `images`, `upscale.model`; cost is fixed at 2. |
| `upscale_tiled` | Diffusion-based tiled upscale | `images`, `upscale.tile_overlap`, `models`, `sampling`, target/desired extents; `passes_count` depends on tile count. |
| `control_image` | Generate a control/preprocessor image | `control_mode`, input/control image. |
| `custom` | Graph workspace execution | `custom_workflow`, optional `models`/`sampling`, images depending on graph placeholders. |

## Core dataclasses

- `WorkflowInput`: top-level request with `kind`, optional `images`, `models`,
  `sampling`, `conditioning`, `inpaint`, `upscale`, `control_mode`,
  `batch_count`, `color_match`, `nsfw_filter`, and `custom_workflow`.
- `ExtentInput`: four extents: `input`, `initial`, `desired`, and `target`.
  `input` is source image/mask resolution; `initial` is first diffusion pass;
  `desired` is high-resolution refinement target; `target` is final canvas
  resolution and may not be a multiple of 8.
- `ImageInput`: image payloads and extents: `initial_image`, `hires_image`,
  `hires_mask`, and `layer_count`. `ImageInput.from_extent(e)` is useful for
  dry-run payload construction.
- `CheckpointInput`: selected checkpoint architecture, VAE, LoRAs, clip skip,
  v-prediction/Zsnr, rescale CFG, self-attention guidance, dynamic caching, and
  tiled VAE flags.
- `SamplingInput`: sampler, scheduler, CFG scale, `total_steps`, `start_step`,
  and seed. `actual_steps == total_steps - start_step`; denoise strength is
  `actual_steps / total_steps`.
- `ConditioningInput`: positive/negative/style prompts, control inputs,
  region-specific prompts, language, and edit-reference flag.
- `ControlInput`: control mode, image, strength, and start/end range.
- `RegionInput`: region mask, bounds, prompt, control list, and LoRAs.
- `InpaintParams`: inpaint mode, target bounds, fill mode, grow/feather/blend,
  and booleans for inpaint model, condition mask, and reference usage.
- `UpscaleInput`: upscaler model name and tile overlap.
- `CustomWorkflowInput`: ComfyUI graph dict, parameter map, evaluated prompts,
  and optional custom style/sampling/model payloads.

## Serialization contract

Use:

```python
data = workflow_input.to_dict()
round_trip = WorkflowInput.from_dict(data)
```

Notes:

- `to_dict(image_format=ImageFileFormat.webp)` serializes image payloads unless
  `image_format=None` is used.
- `to_dict(max_image_size=N)` checks payload size and can fail if embedded image
  data is too large.
- Images/masks are plugin `Image` objects, not PIL/NumPy objects, at this API
  boundary. Convert through `ai_diffusion.image.Image` first.
- `WorkflowInput.merged_prompt` concatenates style, positive prompt, and region
  prompts for request-level summaries.
- `WorkflowInput.passes_count` equals `batch_count` except tiled upscale, where
  it is twice the number of tiles. `cost` uses architecture, pixel count, steps,
  and batch heuristics except fixed-cost control/upscale-simple paths.

## Verified enum values

`WorkflowKind` values in this snapshot:

```text
generate, inpaint, refine, refine_region, upscale_simple, upscale_tiled,
control_image, custom
```

Important related enums:

- `InpaintMode`: `automatic`, `fill`, `expand`, `add_object`, `remove_object`,
  `replace_background`, `custom`.
- `FillMode`: `none`, `neutral`, `blur`, `border`, `replace`, `inpaint`,
  `green`.
- `ControlMode`: `reference`, `style`, `composition`, `face`, `inpaint`,
  `universal`, `scribble`, `line_art`, `soft_edge`, `canny_edge`, `depth`,
  `normal`, `pose`, `segmentation`, `blur`, `stencil`, `hands`.

## Minimal construction pattern

```python
from ai_diffusion.backend.api import (
    CheckpointInput,
    ConditioningInput,
    ImageInput,
    SamplingInput,
    WorkflowInput,
    WorkflowKind,
)
from ai_diffusion.backend.resources import Arch
from ai_diffusion.image import Extent

extent = Extent(512, 512)
work = WorkflowInput(
    kind=WorkflowKind.generate,
    images=ImageInput.from_extent(extent),
    models=CheckpointInput("example.safetensors", Arch.sd15),
    sampling=SamplingInput("dpmpp_2m_sde_gpu", "normal", 7.0, 20, seed=1234),
    conditioning=ConditioningInput("a lighthouse on the beach"),
)
serialized = work.to_dict(image_format=None)
```

If this code fails before constructing `WorkflowInput`, diagnose package import
or Qt setup first using the root environment checker.
