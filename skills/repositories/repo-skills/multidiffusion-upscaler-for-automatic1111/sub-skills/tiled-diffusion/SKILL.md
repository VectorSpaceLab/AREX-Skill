---
name: tiled-diffusion
description: "Configure and troubleshoot the extension's Tiled Diffusion panel
  for MultiDiffusion, Mixture of Diffusers, img2img upscaling, regional prompts,
  noise inversion, ControlNet, and StableSR workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Tiled Diffusion

Use this sub-skill for the **Tiled Diffusion** panel: large txt2img canvases, img2img upscaling/detail enhancement, `MultiDiffusion`, `Mixture of Diffusers`, Regional Prompt Control, Tiled Noise Inversion, and optional ControlNet/StableSR integration.

## When to read

Read this when the user asks about:

- generating a 2K-8K-style image in AUTOMATIC1111 with limited VRAM;
- using the extension as an img2img upscaler/detail enhancer;
- selecting latent tile width/height, overlap, or tile batch size;
- using per-region prompts, seeds, foreground/background boxes, or saved region configs;
- ControlNet tensors with tiled diffusion or moving ControlNet tensor to CPU;
- noise inversion for img2img upscale or why the sampler becomes Euler;
- `UniPC` incompatibility, no-effect Tiled Diffusion runs, seams, tile count, or slow tiled sampling.

For VAE encode/decode memory issues, route to [tiled-vae](../tiled-vae/SKILL.md). For DemoFusion staged multi-scale upscale, route to [demofusion](../demofusion/SKILL.md). For extension loading failures, start at the root [troubleshooting](../../references/troubleshooting.md).

## Quick workflow choice

| Goal | Recommended path |
| --- | --- |
| Large txt2img canvas | Enable Tiled Diffusion, optionally overwrite image size, start with `MultiDiffusion`, use larger overlap for smoother joins, and tune tile batch size for memory. |
| Img2img detail upscale | Enable Tiled Diffusion in img2img, choose an upscaler and scale factor, usually start with `Mixture of Diffusers`, then tune denoise/upscale/overlap. |
| Different prompts in different areas | Use Regional Prompt Control and read [region control](references/region-control.md). |
| Preserve/improve img2img details | Use Noise Inversion cautiously; test on small images and keep denoise low as the UI warning recommends. |
| ControlNet with tiled generation | Keep ControlNet active in WebUI; use `Move ControlNet tensor to CPU` only when VRAM pressure justifies the transfer cost. |

## Important source-backed facts

- The panel is AlwaysVisible in both txt2img and img2img.
- Method choices are `MultiDiffusion` and `Mixture of Diffusers`.
- Default method is `MultiDiffusion` for txt2img and `Mixture of Diffusers` for img2img.
- Latent tile width/height controls range from 16 to 256 in steps of 16; the default is 96.
- Latent tile overlap ranges from 0 to 256 in steps of 4; the default is 48 for txt2img and 8 for img2img.
- Latent tile batch size ranges from 1 to 8; the default is 4.
- Img2img exposes an upscaler dropdown and scale factor from 1.0 to 8.0.
- Noise inversion is img2img-only and the UI warns that default parameters require denoise `<= 0.6`.
- When noise inversion is enabled, the extension switches the sampler to `Euler` because noise inversion only supports that sampler path.
- `MultiDiffusion` asserts that it is not compatible with the `UniPC` sampler.
- If the target canvas is not split into more than one tile and no region/noise-inversion work is active, the extension deliberately ignores tiling.

## References

- [Workflows](references/workflows.md): end-to-end txt2img, img2img, noise inversion, and ControlNet/StableSR recipes.
- [Region control](references/region-control.md): bbox schema, saved config behavior, foreground/background blending, and UI box handling.
- [Troubleshooting](references/troubleshooting.md): sampler conflicts, no-effect runs, ControlNet/StableSR issues, config save/load errors, and performance symptoms.
