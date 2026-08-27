# LatentSync Training Configuration

LatentSync training is config-first. U-Net uses `--unet_config_path`; SyncNet uses `--config_path`. Most shipped configs contain private placeholder paths, so copy a config before editing and keep the original for comparison.

## Shared Runtime Assumptions

- Run from the repository root. Several modules load relative files such as `configs/audio.yaml`, `configs/scheduler_config.json`, and `checkpoints/...`.
- Use a CUDA-capable PyTorch environment for truthful training behavior. The verified inspection stack used Python 3.10 with torch/torchvision CUDA 12.1 wheels, diffusers 0.32.x, transformers 4.48.x, decord, ffmpeg, and setuptools new enough for `pkg_resources`-backed imports.
- The repository has no package metadata. Use module execution from the checkout root (`torchrun -m scripts.train_unet`) or a helper that sets `cwd`/`--repo-root` to the checkout.

## U-Net Config Anatomy

U-Net configs live under `configs/unet/` and contain `data`, `ckpt`, `run`, `optimizer`, and `model` sections.

### `data` Section

Key fields:

- `syncnet_config_path`: path to the SyncNet config copied into the U-Net output directory and loaded for SyncNet supervision when `run.use_syncnet: true`.
- `train_output_dir`: base output directory. The script creates `train-YYYY_MM_DD-HH:MM:SS` below it.
- `train_fileslist`: preferred explicit list of training `.mp4` paths. If non-empty, it takes precedence over `train_data_dir`.
- `train_data_dir`: fallback training directory. In `UNetDataset`, this fallback scans only top-level `.mp4` files.
- `audio_embeds_cache_dir`: cache for Whisper encoder features used by U-Net audio cross-attention.
- `audio_mel_cache_dir`: cache for mel spectrogram tensors used when SyncNet supervision is active.
- `val_video_path`, `val_audio_path`: validation example used to render checkpoint-interval videos.
- `batch_size`, `num_workers`: per-process dataloader settings; shipped U-Net configs use `batch_size: 1`.
- `num_frames`: default `16`; must stay consistent with SyncNet and audio feature slicing unless the architecture is updated.
- `resolution`: `256` or `512`; affects image preprocessing, masks, U-Net sample size, validation generation, and VRAM.
- `mask_image_path`: fixed mask image used by `ImageProcessor`.
- `audio_sample_rate`, `video_fps`: source assumes 16 kHz audio and 25 FPS video.
- `audio_feat_length`: Whisper overlap window, default `[2, 2]`.

### `ckpt` Section

- `resume_ckpt_path`: U-Net checkpoint used for initialization/resume. It must contain a U-Net `state_dict`; shipped configs point to `checkpoints/latentsync_unet.pt`.
- `save_ckpt_steps`: checkpoint and validation interval. U-Net checkpoints are saved as `checkpoints/checkpoint-STEP.pt`.

Do not point `resume_ckpt_path` at a SyncNet checkpoint. If resuming a previous U-Net run, keep the model section compatible with that checkpoint.

### `run` Section

Important gates:

- `pixel_space_supervise`: enables VAE decoding for pixel-space losses. If false, `perceptual_loss_weight` and `trepa_loss_weight` values are effectively inactive.
- `use_syncnet`: enables SyncNet loss when `model.add_audio_layer` is true. Requires `data.syncnet_config_path` to specify `ckpt.inference_ckpt_path` for a compatible SyncNet checkpoint.
- `sync_loss_weight`, `perceptual_loss_weight`, `recon_loss_weight`, `trepa_loss_weight`: loss weights. TREPA loads an auxiliary VideoMAE checkpoint when active; stage2_efficient disables TREPA by setting `trepa_loss_weight: 0`.
- `guidance_scale`, `inference_steps`: validation-video generation settings, not training-time diffusion sampling for the batch loss.
- `trainable_modules`: substring filters applied only when `model.use_motion_module: true`. Stage-2 configs freeze the U-Net and re-enable parameters whose names contain these substrings.
- `use_mixed_noise`, `mixed_noise_alpha`: temporal noise sharing behavior.
- `mixed_precision_training`: enables CUDA autocast and GradScaler.
- `enable_gradient_checkpointing`: saves memory for U-Net; keep enabled for stage-2 and 512px runs unless debugging.
- `max_train_steps`, `max_train_epochs`: `max_train_steps` is used directly unless set to `-1`.

### `optimizer` Section

- `lr`: AdamW learning rate.
- `scale_lr`: if true, multiplies learning rate by the DDP world size.
- `max_grad_norm`: gradient clipping threshold.
- `lr_scheduler`, `lr_warmup_steps`: passed to diffusers `get_scheduler`.

### `model` Section

Key coupling points:

- `add_audio_layer: true` enables audio cross-attention blocks. The shipped configs keep it true.
- `cross_attention_dim`: `384` selects `checkpoints/whisper/tiny.pt`; `768` selects `checkpoints/whisper/small.pt`. Changing this can partially reset cross-attention checkpoint weights.
- `in_channels: 13` corresponds to concatenated noised latents, mask, masked latents, and reference latents.
- `out_channels: 4` predicts latent noise.
- `sample_size: 64` matches SD-VAE latent spatial size for 512px/8 only indirectly; the model code is also driven by input tensors.
- `use_motion_module`: false in stage 1, true in stage 2.
- `motion_module_decoder_only`: true only in `stage2_efficient.yaml`, disabling down-block motion modules while keeping up-block motion modules.
- `motion_module_kwargs`: temporal transformer settings; `temporal_position_encoding_max_len: 24` should cover the default 16 frames.

## U-Net Stage Differences

| Config | `resolution` | `pixel_space_supervise` | `use_syncnet` | `use_motion_module` | `trainable_modules` | Special notes |
| --- | ---: | --- | --- | --- | --- | --- |
| `stage1.yaml` | 256 | false | false | false | not used; all U-Net params train | Latent reconstruction only; documented ~23 GB VRAM. |
| `stage1_512.yaml` | 512 | false | false | false | not used; all U-Net params train | 512px data/checkpoint variant; documented ~30 GB VRAM. |
| `stage2.yaml` | 256 | true | true | true | `motion_modules.`, `attentions.` | Pixel losses, SyncNet loss, TREPA/LPIPS; documented ~30 GB VRAM. |
| `stage2_efficient.yaml` | 256 | true | true | true | `motion_modules.`, `attn2.` | Decoder-only motion modules and audio cross-attention; TREPA disabled; documented ~20 GB VRAM. |
| `stage2_512.yaml` | 512 | true | true | true | `motion_modules.`, `attentions.` | High-VRAM 512px stage-2; documented ~55 GB VRAM; not a smoke target. |

The v1.6 README notes that the 512px release changes data resolution, not model structure or training strategy. Switch configs/checkpoints and `resolution`; do not invent a new architecture just because the output is 512px.

## SyncNet Config Anatomy

SyncNet configs live under `configs/syncnet/` and contain `model`, `ckpt`, `data`, `optimizer`, and `run` sections.

### `model` Section

`model.audio_encoder` and `model.visual_encoder` configure `StableSyncNet` encoder stacks:

- `in_channels`: input channel count.
- `block_out_channels`: channel widths through downsampling blocks.
- `downsample_factors`: per-block spatial downsampling; must collapse to a `D x 1 x 1` feature map for cosine similarity.
- `attn_blocks`: `1` inserts a self-attention block after that down block.
- `dropout`: dropout probability.

From `docs/syncnet_arch.md`: for pixel-space 16-frame SyncNet, `visual_encoder.in_channels = 16 * 3 = 48`; for latent-space 16-frame SyncNet with SD-style 4-channel latents, `visual_encoder.in_channels = 16 * 4 = 64`.

### `ckpt` Section

- `resume_ckpt_path`: actual SyncNet training resume checkpoint, loaded by `scripts.train_syncnet` when non-empty.
- `inference_ckpt_path`: not used by `scripts.train_syncnet`; it is important when a U-Net config loads this SyncNet config for stage-2 SyncNet supervision.
- `save_ckpt_steps`: interval for saving SyncNet checkpoints.

### `data` Section

- `train_output_dir`: base output dir for timestamped SyncNet training runs.
- `num_val_samples`: number of validation samples considered.
- `batch_size`: per-process training batch size. Pixel-space configs default much larger than U-Net configs.
- `gradient_accumulation_steps`: accumulation before optimizer step.
- `latent_space`: if true, frames are VAE-encoded before SyncNet visual encoding.
- `num_frames`: default `16`; must match visual encoder channel math.
- `resolution`: source frame resolution before lower-half cropping or VAE encoding.
- `train_fileslist` / `train_data_dir`: train source. Fileslist takes precedence; directory fallback is recursive for SyncNet.
- `val_fileslist` / `val_data_dir`: validation source. At least one must be non-empty.
- `audio_mel_cache_dir`: mel cache path.
- `lower_half`: crop visual inputs to the lower half before the visual encoder; enabled in pixel-space configs.
- `audio_sample_rate`, `video_fps`: expected 16 kHz and 25 FPS.

### `optimizer` and `run` Sections

- `optimizer.lr`, `optimizer.max_grad_norm`: AdamW and gradient clipping.
- `run.max_train_steps`: total optimizer steps.
- `run.validation_steps`: validation/loss-chart interval.
- `run.mixed_precision_training`: CUDA autocast/GradScaler toggle.
- `run.seed`: rank-offset seed base.

## SyncNet Variant Differences

| Config | `data.latent_space` | `data.lower_half` | Visual channels | Attention | `ckpt.inference_ckpt_path` |
| --- | --- | --- | ---: | --- | --- |
| `syncnet_16_pixel.yaml` | false | true | 48 | none | empty |
| `syncnet_16_pixel_attn.yaml` | false | true | 48 | enabled in deeper audio/visual blocks | `checkpoints/stable_syncnet.pt` |
| `syncnet_16_latent.yaml` | true | false | 64 | none | empty |

Choose a variant based on the representation you want the SyncNet to score. For U-Net stage-2 supervision, the shipped U-Net configs point to `syncnet_16_pixel_attn.yaml` and expect `checkpoints/stable_syncnet.pt` or a compatible replacement.

## Supporting Config Files

- `configs/audio.yaml`: loaded by `latentsync/utils/audio.py`; controls mel spectrogram construction, 80 mel bins, 16 kHz sample rate, STFT window/hop, and normalization.
- `configs/scheduler_config.json`: loaded by `DDIMScheduler.from_pretrained("configs")`; keep it under `configs/` or update the source code.

## Path Replacement Checklist

Before any real launch, replace or confirm:

- `data.train_fileslist` and `data.val_fileslist`, or the corresponding data directories.
- `data.audio_embeds_cache_dir` and `data.audio_mel_cache_dir` to writable locations.
- `data.train_output_dir` to a run-specific output root.
- U-Net `ckpt.resume_ckpt_path` to `checkpoints/latentsync_unet.pt` or a compatible U-Net checkpoint.
- Stage-2 `data.syncnet_config_path` and the referenced SyncNet `ckpt.inference_ckpt_path`.
- U-Net validation media paths and `data.mask_image_path`.
- Auxiliary checkpoint availability for U-Net validation/TREPA when those losses or charts are active.
