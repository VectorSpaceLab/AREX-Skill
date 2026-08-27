# Practical Training Configuration Guide

LTX Trainer configs are YAML files parsed by Pydantic models with `extra="forbid"`; misspelled or misplaced keys fail validation. Start from the nearest template or recreate the sections below, then patch only run-specific values.

Use the bundled validator before launch:

```bash
python path/to/training-workflows/scripts/validate_training_config.py /path/to/config.yaml
```

Use `--relaxed-paths` only while the config still contains placeholder paths. Use strict validation before launching training.

## Top-Level Shape

```yaml
model: { }
lora: { }                 # required only when model.training_mode is "lora"
training_strategy: { }
optimization: { }
acceleration: { }
data: { }
validation: { }
checkpoints: { }
hub: { }
flow_matching: { }
wandb: { }
seed: 42
output_dir: "/path/to/run/outputs"
```

Keep configs in a run workspace or user-approved output directory. Do not mutate template configs when preparing an individual run.

## ModelConfig: Unified vs Split Checkpoint Layout

All model paths are local paths. URLs are not accepted for `model.model_path`.

| Layout | Required keys | Notes |
| --- | --- | --- |
| Unified checkpoint | `model_path`, `text_encoder_path` | `model_path` is one `.safetensors` file containing transformer, video VAE, audio VAE/vocoder, and other model weights. `text_encoder_path` is the matching Gemma model directory. Leave `video_vae_path` and `audio_vae_path` unset. |
| Split LTX 2.5 pack | `model_path`, `text_encoder_path`, usually `video_vae_path`, and audio runs need `audio_vae_path` | `model_path` is the transformer `.safetensors`; `text_encoder_path` is the packed LTX-specific Gemma 4/text-projection `.safetensors`; VAE components are separate files. A video-only run may omit `audio_vae_path`; any run touching audio needs it. |

```yaml
model:
  model_path: "/models/ltx-2.5/diffusion_models/ltx-2.5-22b-dev-transformer-bf16.safetensors"
  text_encoder_path: "/models/ltx-2.5/text_encoders/gemma4-12b-with-proj-ltx-2.5-bf16.safetensors"
  video_vae_path: "/models/ltx-2.5/vae/ltx-2.5-video-vae-bf16.safetensors"
  audio_vae_path: "/models/ltx-2.5/vae/ltx-2.5-audio-vae-bf16.safetensors"
  training_mode: "lora"
  load_checkpoint: null
```

Use the matching text encoder requested by the checkpoint metadata. LTX 2.5 uses the LTX-specific fine-tuned Gemma 4/text-projection pack; do not substitute a vanilla Gemma 4 or a Gemma 3 directory. After switching between LTX-2.3 and LTX 2.5, route dataset reprocessing through `data-preparation` because cached text embeddings are not interchangeable.

## LoraConfig

`lora` is required when `model.training_mode: "lora"` and is not used for full fine-tuning.

```yaml
lora:
  rank: 32
  alpha: 32
  dropout: 0.0
  target_modules:
    - "to_k"
    - "to_q"
    - "to_v"
    - "to_out.0"
```

Keep `alpha == rank` unless the user intentionally requests a different scaling. Choose target modules by mode:

- Audio-video/cross-modal: short patterns `to_k`, `to_q`, `to_v`, `to_out.0`.
- Video-only: `attn1.to_*`, `attn2.to_*`, optional `ff.net.*`.
- Audio-only: `audio_attn1.to_*`, `audio_attn2.to_*`, `audio_ff.*`.

Changing rank, target modules, or training mode affects resume compatibility. If loading old weights but intentionally discarding optimizer/scheduler state, set `checkpoints.no_resume: true` and explain that it is not a full resume.

## TrainingStrategyConfig

Prefer `training_strategy.name: "flexible"`.

```yaml
training_strategy:
  name: "flexible"
  video:
    is_generated: true
    latents_dir: "latents"
    conditions: []
  audio:
    is_generated: true
    latents_dir: "audio_latents"
    conditions: []
```

Rules:

- At least one modality must have `is_generated: true`.
- Omit the modality block for audio-only or video-only modes.
- `latents_dir`, `mask_dir`, and reference `latents_dir` are directory names under `data.preprocessed_data_root`.
- Audio conditions cannot be `first_frame` or `spatial_crop`.
- `conditions/` text embeddings are always required under `preprocessed_data_root`.

## OptimizationConfig

```yaml
optimization:
  learning_rate: 1e-4
  steps: 2000
  batch_size: 1
  gradient_accumulation_steps: 1
  max_grad_norm: 1.0
  optimizer_type: "adamw"          # or "adamw8bit"
  scheduler_type: "linear"        # constant, linear, cosine, cosine_with_restarts, polynomial, step
  scheduler_params: { }
  enable_gradient_checkpointing: true
```

For memory pressure, first use gradient checkpointing, batch size 1, gradient accumulation, `adamw8bit`, and acceleration quantization before reducing resolution or reprocessing. Do not claim a quality outcome from these settings.

## AccelerationConfig

```yaml
acceleration:
  mixed_precision_mode: "bf16"     # "no", "fp16", or "bf16"
  quantization: null               # null, "int8-quanto", "int4-quanto", "int2-quanto", "fp8-quanto", "fp8uz-quanto"
  load_text_encoder_in_8bit: false
  offload_optimizer_during_validation: false
```

Important distinctions:

- `acceleration.load_text_encoder_in_8bit` affects the trainer's validation-prompt embedding cache at training startup.
- Dataset preprocessing may have its own text-encoder 8-bit flag; that belongs to `data-preparation`.
- `offload_optimizer_during_validation` can help validation OOM for full fine-tunes or high-rank LoRAs; it has no effect for FSDP.
- Backend package choices and kernel installation route to `performance-backends`.

## DataConfig

```yaml
data:
  preprocessed_data_root: "/path/to/run/dataset/.precomputed"
  num_dataloader_workers: 2
```

The data root must already exist and contain every directory required by the strategy: `conditions/`, generated/frozen modality latents, and any `mask_dir` or `reference` latent directories. If raw media or metadata needs processing, route to `data-preparation` first.

## ValidationConfig

```yaml
validation:
  samples:
    - prompt: "A detailed validation prompt describing the visual action and audio when audio is generated."
      conditions: []
  video_dims: [960, 544, 89]
  frame_rate: 24.0
  seed: 42
  inference_steps: 30
  interval: 100
  video_cfg_scale: 3.0
  audio_cfg_scale: 7.0
  video_stg_scale: 1.0
  audio_stg_scale: 1.0
  stg_blocks: [28]
  guidance_rescale: 0.7
  video_modality_guidance_scale: 3.0
  audio_modality_guidance_scale: 3.0
  generate_audio: true
  generate_video: true
  skip_initial_validation: false
```

Checks before launch:

- Width and height should be divisible by the VAE spatial factor, commonly 32.
- Default VAE frame counts commonly satisfy `frames % 8 == 1`.
- If `generate_video: false`, keep `generate_audio: true` when validation samples exist.
- For V2A, use `video_to_audio` validation conditions and usually `generate_video: false`.
- For A2V, use `audio_to_video` validation conditions and usually `generate_audio: false`.
- For audio-generating runs, validation prompts should describe the target audio in the same style as training captions.

## CheckpointsConfig

```yaml
checkpoints:
  interval: 250
  keep_last_n: 3
  precision: bfloat16
  no_resume: false
  save_training_state: "minimal"  # "full", "minimal", or "off"
```

`model.load_checkpoint` controls which weights are loaded. Resume state is found only next to that loaded checkpoint and only when `checkpoints.no_resume: false`. `save_training_state: "minimal"` stores scheduler/RNG/step information and is commonly enough for LoRA resume; `"full"` includes optimizer state and can be much larger; `"off"` disables resume state.

## HubConfig and WandbConfig

```yaml
hub:
  push_to_hub: false
  hub_model_id: "username/model-name"

wandb:
  enabled: false
  project: "ltx-2-trainer"
  entity: null
  tags: []
  log_validation_videos: true
```

Hub upload requires a valid `hub_model_id` and Hugging Face write credentials. W&B logging requires credentials accepted by the `wandb` package. Do not print or store tokens in configs or logs.

## FlowMatchingConfig

```yaml
flow_matching:
  timestep_sampling_mode: "shifted_logit_normal"  # or "uniform"
  timestep_sampling_params: { }
```

Only change flow-matching settings when the user intentionally wants a sampler experiment. If changing them during a resumed run, explain that resume-state compatibility may be affected.

## Safe Patching Checklist

1. Copy or create the run config in the user-approved workspace.
2. Patch `model.*` local paths, `data.preprocessed_data_root`, `output_dir`, validation samples, and logging/upload settings.
3. Match `training_strategy` and `lora.target_modules` to the selected mode from `training-modes.md`.
4. Use `validate_training_config.py --relaxed-paths` while editing placeholders.
5. Verify real model, component, data, and validation paths with strict validation before launch.
6. Build, show, and get approval for the command before running training.
