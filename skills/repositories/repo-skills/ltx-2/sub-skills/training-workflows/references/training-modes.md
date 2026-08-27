# Training Modes and Flexible Strategy Semantics

The LTX Trainer expresses current training modes through `training_strategy.name: "flexible"`. A mode is defined by which modality blocks exist, whether each modality is generated or frozen, and which conditions are attached.

## Flexible Strategy Semantics

| Config field | Meaning |
| --- | --- |
| `training_strategy.name: "flexible"` | Use the unified strategy for text, video, audio, intrinsic conditioning, frozen cross-modal conditioning, and IC-LoRA reference conditioning. Legacy strategies may still parse but new configs should use `flexible`. |
| `video` / `audio` block present | The trainer loads that modality's precomputed latent directory from `data.preprocessed_data_root`. Omit a modality block when the mode is truly video-only or audio-only. |
| `is_generated: true` | The modality is denoised during training, contributes targets, and contributes to the loss. |
| `is_generated: false` | The modality stays clean with sigma/timestep 0, contributes no loss, and acts as conditioning for the generated modality. |
| `latents_dir` | Directory name under `preprocessed_data_root`, not an arbitrary external path. Common names are `latents` for video and `audio_latents` for audio. |
| `conditions` | Per-modality condition list. Conditions can be composed when their semantics are compatible. Text conditioning is implicit through `conditions/`. |

At least one configured modality must have `is_generated: true`. Audio supports `prefix`, `suffix`, `mask`, and `reference`; audio does **not** support `first_frame` or `spatial_crop`.

## Condition Semantics

| Condition | Training fields | Modality support | Training behavior |
| --- | --- | --- | --- |
| `first_frame` | `probability` | Video only | First latent frame is clean, timestep 0, and excluded from loss when applied. |
| `prefix` | `temporal_boundary`, `probability` | Video or audio | First N latent temporal units are clean, timestep 0, and excluded from loss. Used for forward extension. |
| `suffix` | `temporal_boundary`, `probability` | Video or audio | Last N latent temporal units are clean, timestep 0, and excluded from loss. Used for backward extension. |
| `spatial_crop` | `spatial_region: [y1, x1, y2, x2]`, `probability` | Video only | Pixel rectangle is converted to latent coordinates, kept clean, timestep 0, and excluded from loss. |
| `mask` | `mask_dir`, `probability` | Video or audio | Per-sample masks are thresholded at 0.5; mask value 1 means conditioning/clean, value 0 means generated/loss. |
| `reference` | `latents_dir`, `probability` | Video or audio | Precomputed reference latents are prepended as clean IC-LoRA tokens, timestep 0, and excluded from loss. |

Training condition paths are directory names under `preprocessed_data_root`. Validation conditions use individual media/mask files and are mapped separately below.

## Mode Table

| User task | Mode | Strategy blocks | Conditions | Expected latent directories | Target modules |
| --- | --- | --- | --- | --- | --- |
| Generate video+audio from text, general audiovisual LoRA | T2V | `video.is_generated: true`, `audio.is_generated: true` | none | `conditions/`, `latents/`, `audio_latents/` | Short AV patterns: `to_k`, `to_q`, `to_v`, `to_out.0`. |
| Animate from a starting image, or plain concept/style LoRA when user wants image use or is unsure | I2V | video generated, audio generated | `video.conditions: [{type: first_frame, probability: 0.5}]` in the shipped-style config | `conditions/`, `latents/`, `audio_latents/` | Short AV patterns. |
| Extend video forward | Video extension | video generated, audio generated | `video.prefix` | `conditions/`, `latents/`, `audio_latents/` | Short AV patterns. |
| Extend video backward | Video suffix extension | video generated, audio generated | `video.suffix` | `conditions/`, `latents/`, `audio_latents/` | Short AV patterns. |
| Paired video transformation, control adapter, style transfer, deblur/color/depth/pose IC-LoRA | V2V IC-LoRA | `video.is_generated: true`; omit audio by default | `video.reference` with `latents_dir: reference_latents` | `conditions/`, `latents/`, `reference_latents/` | Explicit video patterns: `attn1.*`, `attn2.*`, optional `ff.net.*`. |
| Generate video conditioned on frozen audio | A2V | `video.is_generated: true`, `audio.is_generated: false` | none | `conditions/`, `latents/`, `audio_latents/` | Short AV patterns because cross-modal attention matters. |
| Generate audio/Foley conditioned on frozen video | V2A | `video.is_generated: false`, `audio.is_generated: true` | none | `conditions/`, `latents/`, `audio_latents/` | Short AV patterns because cross-modal attention matters. |
| Fill masked video regions | Video inpainting | `video.is_generated: true`; omit audio by default | `video.mask` with `mask_dir: video_masks` | `conditions/`, `latents/`, `video_masks/` | Video-only patterns unless joint audio is explicitly added. |
| Expand video outside a crop | Video outpainting | `video.is_generated: true`; omit audio by default | `video.spatial_crop` | `conditions/`, `latents/` | Video-only patterns unless joint audio is explicitly added. |
| Generate audio from text | T2A | `audio.is_generated: true`; omit video | none | `conditions/`, `audio_latents/` | Explicit audio patterns: `audio_attn1.*`, `audio_attn2.*`, `audio_ff.*`. |
| Extend audio forward | Audio extension | `audio.is_generated: true`; omit video | `audio.prefix` | `conditions/`, `audio_latents/` | Explicit audio patterns. |
| Extend audio backward | Audio suffix extension | `audio.is_generated: true`; omit video | `audio.suffix` | `conditions/`, `audio_latents/` | Explicit audio patterns. |
| Fill masked audio region | Audio inpainting | `audio.is_generated: true`; omit video | `audio.mask` with `mask_dir: audio_masks` | `conditions/`, `audio_latents/`, `audio_masks/` | Explicit audio patterns. |
| Audio reference/style transformation | A2A IC-LoRA | `audio.is_generated: true`; omit video | `audio.reference` with `latents_dir: reference_audio_latents` | `conditions/`, `audio_latents/`, `reference_audio_latents/` | Explicit audio patterns. |
| Joint audio-video reference transformation | AV2AV IC-LoRA | video generated, audio generated | `video.reference`, `audio.reference` | `conditions/`, `latents/`, `audio_latents/`, `reference_latents/`, `reference_audio_latents/` | Short AV patterns. |
| Full model fine-tune for any supported mode | Full fine-tune | Same strategy as selected mode | Same as selected mode | Same as selected mode | Set `model.training_mode: "full"`; `lora` is not used. |

Do not promise that one mode will produce better results. Choose the mode from the user's intended input/output contract and the data they can actually provide.

## Target Module Families

Use exact module-name patterns; avoid broad patterns for audio-only/video-only modes unless the user deliberately wants to train extra branches.

### Audio-video or cross-modal modes

```yaml
lora:
  target_modules:
    - "to_k"
    - "to_q"
    - "to_v"
    - "to_out.0"
```

These short patterns match video attention, audio attention, and audio-video cross-attention modules.

### Video-only modes

```yaml
lora:
  target_modules:
    - "attn1.to_k"
    - "attn1.to_q"
    - "attn1.to_v"
    - "attn1.to_out.0"
    - "attn2.to_k"
    - "attn2.to_q"
    - "attn2.to_v"
    - "attn2.to_out.0"
    # Optional capacity knobs, not automatic promises:
    # - "ff.net.0.proj"
    # - "ff.net.2"
```

### Audio-only modes

```yaml
lora:
  target_modules:
    - "audio_attn1.to_k"
    - "audio_attn1.to_q"
    - "audio_attn1.to_v"
    - "audio_attn1.to_out.0"
    - "audio_attn2.to_k"
    - "audio_attn2.to_q"
    - "audio_attn2.to_v"
    - "audio_attn2.to_out.0"
    - "audio_ff.net.0.proj"
    - "audio_ff.net.2"
```

## Training-to-Validation Condition Mapping

`validation.samples` are self-describing. The condition `type` names overlap with training conditions, but validation references individual media files instead of precomputed latent directories.

| Training mode/condition | Validation shape |
| --- | --- |
| T2V or T2A | `samples: [{prompt: "...", conditions: []}]`; set `generate_video`/`generate_audio` to match what should be sampled. |
| I2V `first_frame` | `conditions: [{type: first_frame, image_or_video: "/path/to/image-or-video"}]`. If the path is a video, the first frame is used. |
| Video prefix/suffix | `conditions: [{type: prefix, video: "/path/to/context.mp4", num_frames: 25}]` or `suffix`; use VAE-aligned frame counts. |
| Audio prefix/suffix | `conditions: [{type: prefix, audio: "/path/to/context.wav", duration: 2.5}]` or `suffix`. |
| Video outpainting | `conditions: [{type: spatial_crop, video: "/path/to/context.mp4", spatial_region: [y1, x1, y2, x2]}]`. |
| Video/audio inpainting | `conditions: [{type: mask, video: "/path/to/video.mp4", mask: "/path/to/mask.mp4"}]` or use `audio` plus an audio mask file. |
| V2V IC-LoRA | `conditions: [{type: reference, video: "/path/to/reference.mp4", downscale_factor: 1, temporal_scale_factor: 1, include_in_output: true}]`; scale factors must match preprocessing if references were downscaled. |
| A2A IC-LoRA | `conditions: [{type: reference, audio: "/path/to/reference.wav"}]`. |
| AV2AV IC-LoRA | Include separate `reference` entries for video and audio reference files. |
| A2V | `conditions: [{type: audio_to_video, audio: "/path/to/audio.wav"}]`; usually `generate_video: true`, `generate_audio: false` for validation. |
| V2A | `conditions: [{type: video_to_audio, video: "/path/to/video.mp4"}]`; usually `generate_video: false`, `generate_audio: true` for validation. |

Validation `video_dims` must use width/height divisible by the VAE spatial factor (32 by default) and frame counts that satisfy the VAE temporal alignment rule, commonly `frames % 8 == 1` for the default VAE.
