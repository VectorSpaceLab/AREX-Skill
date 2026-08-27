---
name: tiled-vae
description: "Configure and troubleshoot the extension's Tiled VAE panel for
  high-resolution VAE encode/decode, tile-size tuning, fast modes, attention
  backend compatibility, NaN, and OOM recovery."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Tiled VAE

Use this sub-skill when the user's task concerns **Tiled VAE**: decoding/encoding very large images, VAE out-of-memory failures, fp16 NaNs, encoder/decoder tile sizes, fast encoder/decoder modes, color fix, or WebUI attention optimization compatibility.

## When to read

Read this for:

- CUDA OOM during VAE encode/decode rather than during UNet denoising;
- 4K/8K image decode or img2img encode where regular VAE fails;
- selecting encoder and decoder tile sizes based on VRAM;
- deciding whether to move VAE to GPU;
- interpreting fast encoder, fast decoder, and fast encoder color fix;
- NaNs with half VAE or unknown attention optimization warnings.

For tiled denoising, region prompts, or img2img upscale settings, read [tiled-diffusion](../tiled-diffusion/SKILL.md). For DemoFusion staged upscale, read [demofusion](../demofusion/SKILL.md).

## Core operating facts

- The panel is AlwaysVisible in both txt2img and img2img.
- Enabling Tiled VAE replaces the active VAE encoder/decoder `forward` methods with tiled hooks for the duration of processing, then restores them in postprocess.
- The encoder uses padding of 32 pixels; the decoder uses padding of 11 latent pixels.
- If an input is small enough for the selected tile size, the hook prints that tiling is unnecessary and falls back to the original VAE forward.
- Recommended tile sizes are computed from CUDA device memory when available; CPU defaults are conservative.
- The source comments warn that fp16 VAE can produce NaNs for giant images and recommends `--no-half-vae` for those cases.

## References

- [Workflows](references/workflows.md): setup, tile-size defaults, fast mode semantics, and validation steps.
- [Troubleshooting](references/troubleshooting.md): OOM, NaN, attention backend, stale hook, and performance recovery.
