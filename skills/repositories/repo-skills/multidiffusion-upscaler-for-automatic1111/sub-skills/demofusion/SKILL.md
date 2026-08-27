---
name: demofusion
description: "Configure and troubleshoot the extension's DemoFusion panel for
  staged multi-scale upscaling, local/global windows, random jitter, mixture
  mode, noise inversion, and ControlNet/StableSR interop."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# DemoFusion

Use this sub-skill for the extension's separate **DemoFusion** panel. DemoFusion performs staged multi-scale denoising/upscaling with local tiled windows and global views. It is not the same route as the Tiled Diffusion panel.

## When to read

Read this when the user asks about:

- enabling DemoFusion in AUTOMATIC1111;
- staged x2/x3/x4 upscale behavior;
- latent window size, overlap, local/global batch sizes;
- random jitter, mixture mode, Gaussian filter, cosine scales, or sigma;
- DemoFusion with img2img, keep-input-size, or noise inversion;
- why the panel says not to open DemoFusion with Tiled Diffusion;
- DemoFusion `UniPC` incompatibility, speed, OOM, or image-size infotext behavior.

For normal Tiled Diffusion/MultiDiffusion/Mixture of Diffusers, route to [tiled-diffusion](../tiled-diffusion/SKILL.md). For VAE encode/decode OOM, route to [tiled-vae](../tiled-vae/SKILL.md).

## Core operating facts

- The panel title is **DemoFusion**.
- The UI text warns: do not open DemoFusion with Tiled Diffusion.
- The only method choice is `DemoFusion`.
- DemoFusion asserts that it is not compatible with `UniPC`.
- Scale factor is used as an integer staged upscale count.
- Window size defaults to 128 and is bounded by the latent canvas size.
- Window overlap defaults to 64.
- Local tile batch size and global window batch size both default to 4.
- Random jitter defaults on.
- Cosine scale defaults are `3`, `1`, and `1`; sigma defaults to `0.6`.
- Txt2img exposes denoising strength for the substage with default `0.85`.

## References

- [Workflows](references/workflows.md): basic txt2img/img2img DemoFusion setup, staged upscale controls, and parameter meanings.
- [Troubleshooting](references/troubleshooting.md): conflict with Tiled Diffusion, sampler incompatibility, stochastic jitter, OOM, and slow staged runs.
