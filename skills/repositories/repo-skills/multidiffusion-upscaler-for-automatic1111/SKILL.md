---
name: multidiffusion-upscaler-for-automatic1111
description: "Use the Tiled Diffusion & VAE AUTOMATIC1111 WebUI extension for
  large-image txt2img/img2img, tiled VAE, regional prompts, noise inversion,
  ControlNet/StableSR interop, and DemoFusion workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Tiled Diffusion & VAE extension for AUTOMATIC1111

Use this repo skill when a task involves the `multidiffusion-upscaler-for-automatic1111` extension, AUTOMATIC1111 Tiled Diffusion, Tiled VAE, MultiDiffusion, Mixture of Diffusers, DemoFusion, region prompt control, or noise-inversion-assisted img2img upscaling.

This skill is source-backed operating guidance for a WebUI extension. It is not a standalone Python package manual: the extension scripts expect the AUTOMATIC1111 WebUI runtime, its `modules` package, a loaded Stable Diffusion model, and the WebUI sampler/device abstractions.

## When to load this skill

Load this skill for tasks such as:

- Installing or checking this extension in an AUTOMATIC1111 WebUI setup.
- Choosing between Tiled Diffusion, Tiled VAE, and DemoFusion for a large-image task.
- Configuring latent tile sizes, overlap, tile batch size, upscale factor, or VAE encoder/decoder tile sizes.
- Debugging seams, no-effect runs, OOM/NaN failures, bad region prompt boxes, stale region config files, or sampler conflicts.
- Explaining how this extension interacts with ControlNet, StableSR, SDXL-style conditioning, or WebUI attention optimizations.

Avoid this skill when the task is only generic Stable Diffusion prompting, a Diffusers pipeline, ComfyUI node graph, generic AUTOMATIC1111 launch/API behavior, LoRA training, or image upscaling outside this extension.

## Runtime model and availability checks

- This project is installed as an AUTOMATIC1111 WebUI extension, normally by adding the extension folder under WebUI `extensions/` or using WebUI's extension installer. Do **not** treat it as a `pip install` package.
- A plain `python -c "import scripts.tilediffusion"` check outside WebUI is expected to fail because WebUI provides the `modules.*` imports at runtime.
- After a WebUI restart, the practical availability check is that the txt2img/img2img UI exposes panels named **Tiled Diffusion**, **Tiled VAE**, and **DemoFusion**.
- Real image generation requires a working WebUI model environment and a Torch backend. The repo targets large images on limited VRAM, but generation is still backend/model dependent.
- Read [setup and compatibility](references/setup-and-compatibility.md) before changing installation, WebUI version, accelerator backend, ControlNet/StableSR, or model/VAE assumptions.

## Route map

| Task | Read next | Notes |
| --- | --- | --- |
| Large txt2img canvas, img2img upscaling/detail enhancement, MultiDiffusion vs Mixture of Diffusers, regional prompts, noise inversion | [tiled-diffusion](sub-skills/tiled-diffusion/SKILL.md) | Covers the main `Tiled Diffusion` panel and its extra controls. |
| VAE encode/decode OOM, 8K decode, fast encoder/decoder, `--no-half-vae`, attention backend issues | [tiled-vae](sub-skills/tiled-vae/SKILL.md) | Covers the `Tiled VAE` panel and VAE hook behavior. |
| DemoFusion staged upscale, random jitter, global/local windows, integer scale factors, conflict with Tiled Diffusion | [demofusion](sub-skills/demofusion/SKILL.md) | Covers the separate `DemoFusion` panel. |
| Extension missing from WebUI, standalone import errors, optional integration not detected, license/runtime constraints | [root troubleshooting](references/troubleshooting.md) | Use before feature-specific debugging if the extension itself may not be loaded. |
| Checking whether this skill matches a checkout or should be refreshed | [repo provenance](references/repo-provenance.md) | Contains commit, dirty-state, and evidence-path baseline. |

## Cross-cutting operating rules

1. Do not run extension entrypoint scripts outside WebUI as standalone programs; they hook WebUI sampler/VAE/global model objects.
2. Do not enable **Tiled Diffusion** and **DemoFusion** together for the same generation. The DemoFusion UI explicitly warns not to open it with Tiled Diffusion.
3. Prefer source-backed panel names and option names when constructing user guidance; many controls are stored in PNG info under `Tiled Diffusion` or patched infotext fields.
4. Treat ControlNet and StableSR support as opportunistic integration: the extension detects those scripts if they are already present in WebUI.
5. For very large images, distinguish UNet/sampler tiling from VAE tiling. Tiled Diffusion changes denoising; Tiled VAE changes encoding/decoding memory behavior.
6. The repo code is licensed CC BY-NC-SA 4.0; the README states post-2023-03-28 versions may not be used for commercial sale of the repo code.

## References

- [Setup and compatibility](references/setup-and-compatibility.md): installation model, host/runtime requirements, backend assumptions, and optional integrations.
- [Root troubleshooting](references/troubleshooting.md): extension-level failures before entering a specific feature route.
- [Repository provenance](references/repo-provenance.md): refresh baseline and evidence inventory.
