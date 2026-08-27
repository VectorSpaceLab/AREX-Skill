---
name: conditioning
description: "Use diffusion wrapper models conditioned on lower-rate waveforms,
  mel spectrograms, latents, and transform plugins."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Conditioning

Use this sub-skill when the task is about diffusion wrappers that condition generation on another audio representation.

## Route here when the request mentions
- audio upsampling or super-resolution
- waveform to mel vocoding
- diffusion autoencoding or latent conditioning
- encoder, adapter, mel, or transform wrapper setup
- `AppendChannelsPlugin` or `LTPlugin`

## Route to `../generation` instead when the task is about
- base unconditional generation
- text-conditioned generation
- inpainting
- core UNet, diffusion, or sampler configuration that is not wrapper-specific

## What to open first
- `references/api-reference.md` for constructors, prefixes, and shape contracts
- `references/workflows.md` for upsampler, vocoder, and autoencoder recipes
- `references/troubleshooting.md` for prefix, shape, and dependency fixes
- `scripts/tiny_conditioning_smoke.py` for a safe CPU smoke run

## Quick map
- Upsampler: `DiffusionUpsampler`
- Vocoder: `DiffusionVocoder`
- Autoencoder: `DiffusionAE`
- Encoder contract: `EncoderBase`
- Adapter hooks: `AdapterBase`
- Mel helper: `MelSpectrogram`
- Transform helpers: `AppendChannelsPlugin`, `LTPlugin`

The bundled smoke uses a local dummy encoder and stays away from optional external encoder packages.
