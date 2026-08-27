# Pyramid-Flow Model Overview

Pyramid-Flow is a flow-matching video generation repository built around a pyramidal DiT, a causal video VAE, custom schedulers, and distributed helpers for inference and training.

## Component graph

```text
prompt / image / precomputed text features
        |
        v
   text encoder(s)
        |
        v
PyramidDiTForVideoGeneration
  |-- `pyramid_flux` or `pyramid_mmdit`
  |-- PyramidFlowMatchEulerDiscreteScheduler
  |-- CausalVideoVAE
  `-- trainer_misc distributed helpers
        |
        v
latent sequence -> VAE decode -> frames / PIL images / MP4 export
```

## Model families

| Family | Typical use | Notes |
| --- | --- | --- |
| `pyramid_flux` | miniFLUX-style checkpoints, 384p video paths, and the image variant | Best fit for the smaller public generation route and the text-to-image/image variant. |
| `pyramid_mmdit` | SD3/MMDiT-style checkpoints and the 768p path | Best fit for the higher-resolution video route and broader multi-GPU inference support. |
| Causal Video VAE | Encode, decode, and reconstruct video or one-frame image inputs | Used for latent extraction, latent decoding, and VAE training. |
| Flow scheduler | Stage-based reverse diffusion / flow matching | The scheduler is stage-aware and is paired with the pyramidal generation flow. |

## Workflow families

| Workflow family | Primary sub-skill | What it owns |
| --- | --- | --- |
| Model-component inspection | `sub-skills/core-components/` | `PyramidDiTForVideoGeneration`, `CausalVideoVAE`, `CausalVideoVAELossWrapper`, schedulers, and distributed helpers. |
| Generation and inference | `sub-skills/generation-inference/` | Prompt-to-video, image-to-video, text-to-image, Gradio demos, and multi-GPU inference planning. |
| Data preparation | `sub-skills/data-preparation/` | JSONL schemas, dataset loading, text features, VAE latents, and tiny fixture checks. |
| Training workflows | `sub-skills/training-workflows/` | DiT AR/non-AR training, two-stage Causal VAE training, and launch prerequisites. |

## Resolution and layout notes

- Video generation is organized around 384p and 768p paths.
- The image variant returns images rather than a video timeline.
- The Causal VAE uses an 8x spatial downsample, so height and width should be divisible by 8 for workflow planning.
- Multi-GPU launchers use `torchrun` plus sequence-parallel / distributed helper logic.

## Use this overview

Read this file before deciding which sub-skill owns a task. Use the detailed sub-skill references for exact signatures, command shapes, data schemas, and troubleshooting.
