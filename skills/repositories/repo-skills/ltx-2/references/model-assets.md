# LTX Model Assets

## When to read

Read this before building inference, preprocessing, or training commands. Most LTX failures come from mixing checkpoint layouts, missing local component files, or using the wrong Gemma text encoder.

## LTX-2.5 split layout

LTX-2.5 is the recommended current layout in this skill. Its Hugging Face repository publishes one file per component. A typical local folder keeps the upstream component directories:

```text
models/ltx-2.5/
  diffusion_models/
    ltx-2.5-22b-dev-transformer-bf16.safetensors
    ltx-2.5-22b-distilled-transformer-bf16.safetensors
  text_encoders/
    gemma4-12b-with-proj-ltx-2.5-bf16.safetensors
  vae/
    ltx-2.5-video-vae-bf16.safetensors
    ltx-2.5-video-vae-conv-bf16.safetensors
    ltx-2.5-audio-vae-bf16.safetensors
  latent_upscale_models/
    ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0.safetensors
    ltx-2.5-latent-temporal-upscaler-x2-bf16-1.0.safetensors
  loras/
    ltx-2.5-22b-distilled-lora-450-bf16.safetensors
  model_patches/
    ltx-2.5-duration-head-bf16.safetensors
```

Important rules:

- `--transformer-path` points at a transformer only. It does not contain VAE or text encoder weights.
- `--text-encoder-path` points at the packed LTX-specific Gemma 4 text-encoder `.safetensors`; do not substitute Google's vanilla Gemma 4.
- `--video-vae-path` is required when a split workflow encodes/decodes video.
- `--audio-vae-path` is required when a split workflow touches audio or generates audio.
- Two-stage pipelines require the spatial upsampler. DFR temporal rounds also require the temporal upsampler.
- Guided full-model two-stage pipelines need the distilled LoRA for the refinement stage; `DistilledPipeline`, `ICLoraPipeline`, and `DubItPipeline` use distilled-model-specific paths.

## LTX-2.3 / legacy monolith layout

Legacy and LTX-2.3 flows use one large `.safetensors` checkpoint for transformer, video VAE, audio VAE, and text projection, plus a matching Gemma directory. Typical CLI flags look like:

```bash
--checkpoint-path /models/ltx-2.3-22b-dev.safetensors \
--gemma-root /models/gemma-3-12b-it
```

Rules:

- The monolith checkpoint and Gemma directory must match the checkpoint metadata.
- LTX-2.3 LoRAs are not interchangeable with LTX-2.5 LoRAs.
- LTX-2.3 text embeddings should not be reused after switching a dataset to LTX-2.5.

## Layout XOR rule

Pipeline CLIs accept either monolith flags or split flags, not both:

- Monolith: `--checkpoint-path` or `--distilled-checkpoint-path` plus `--gemma-root`.
- Split: one or more component flags such as `--transformer-path`, `--text-encoder-path`, `--audio-vae-path`, and optional `--duration-head-path`; `--video-vae-path` fills the video VAE slot in either mode.

If a command mixes split pack flags with `--checkpoint-path` / `--distilled-checkpoint-path` / `--gemma-root`, rebuild the command from one layout.

## Asset acquisition boundaries

- Model repositories may be gated. If a download returns 401/403, accept the model terms and use a Hugging Face token with read access to gated repos.
- Downloads are tens of GiB. Do not auto-download assets in an agent workflow unless the user explicitly approves the network use, destination, and disk cost.
- The generated skill assumes local paths supplied by the user. It does not embed model files.

## Preprocessing and training implications

- Preprocessing with LTX-2.5 split transformers requires the same split components as training: transformer, text encoder, video VAE, and audio VAE when audio is involved.
- Existing `.precomputed/conditions` were produced by a specific Gemma model. Regenerate them when switching between LTX-2.3/Gemma 3 and LTX-2.5/Gemma 4.
- The checkpoint's VAE metadata determines the actual spatial and temporal factors. The common default is spatial factor 32 and temporal factor 8.

## Choosing assets by route

| Route | Usually needed |
| --- | --- |
| Fast distilled T2V/I2V | Distilled transformer, packed text encoder, video VAE, audio VAE, spatial upsampler. |
| Guided two-stage TI2V/HQ | Dev/full transformer or monolith, matching text encoder/Gemma, video/audio VAE, distilled LoRA, spatial upsampler. |
| DFR | Full transformer, text encoder, video/audio VAE, distilled LoRA, spatial upsampler, optional temporal upsampler, optional detailing LoRA. |
| Retake | Source video, transformer/monolith or split components, text encoder, VAEs; source media must satisfy frame/dimension constraints. |
| Trainer preprocessing | Model/transformer path, matching text encoder path, video VAE path for split video data, audio VAE path for split audio data. |
| Training | Same model family as preprocessing plus config paths to precomputed data; optional LoRA checkpoint for resume. |
