# Model Family Guide

Use this guide to prevent script/flag mismatches when composing sd-scripts training commands.

## Stable Diffusion 1.x and 2.x

- LoRA/additional networks use `train_network.py`.
- Full DreamBooth-style training uses `train_db.py`; metadata/caption fine-tuning uses `fine_tune.py`; embeddings use `train_textual_inversion.py`.
- Common base flag: `--pretrained_model_name_or_path path/to/model.safetensors`.
- SD2 v-prediction checkpoints need `--v2 --v_parameterization`.
- SD1 checkpoints should not receive SD2 v-prediction flags.
- Attention choices are commonly `--xformers`, `--sdpa`, or memory-efficient attention depending on installed packages.

## SDXL

- LoRA/additional networks use `sdxl_train_network.py`.
- SDXL ControlNet-LLLite uses `sdxl_train_control_net_lllite.py` and is experimental.
- LECO slider training uses `sdxl_train_leco.py`.
- Do not use SD1/2 `--v2` or `--v_parameterization` flags.
- `--cache_text_encoder_outputs` is strongly useful for VRAM and speed when not training text encoders, but it disables caption augmentations.
- `--no_half_vae` can help with VAE numerical issues at the cost of VRAM.

## SD3 / SD3.5

- Use `sd3_train_network.py` for LoRA/additional networks.
- SD3 uses MMDiT and up to three text encoders; separate `--clip_l`, `--clip_g`, `--t5xxl`, and `--vae` paths may be needed unless the checkpoint is a single file with embedded components.
- `--t5xxl_max_token_length` controls the T5-XXL token length; default is commonly 256.
- `--apply_t5_attn_mask` applies attention masks to T5XXL outputs.
- `--clip_l_dropout_rate`, `--clip_g_dropout_rate`, and `--t5_dropout_rate` are SD3 text-encoder dropout controls.
- `--cache_text_encoder_outputs` is recommended when text encoders are not being trained.
- `--blocks_to_swap` can reduce VRAM but conflicts with `--cpu_offload_checkpointing`.
- Do not use SD1/2 flags `--v2`, `--v_parameterization`, or `--clip_skip`.

## FLUX.1

- Use `flux_train_network.py` with `--network_module networks.lora_flux`.
- Required assets: FLUX `.safetensors` DiT/model, CLIP-L, T5XXL, AE, and dataset config.
- Diffusers-format subfolders are not the intended direct input for the FLUX model path; use supported `.safetensors` files.
- Recommended training choices often include `--guidance_scale 1.0`, `--timestep_sampling flux_shift`, and `--model_prediction_type raw`.
- `--fp8_base` and fp8 T5XXL checkpoints reduce memory; `--fp8_base_unet` trains the FLUX model in fp8 while keeping text encoders in bf16/fp16.
- `--blocks_to_swap` saves VRAM; FLUX supports a high number of swapped blocks, but training slows as swaps increase.
- `--cpu_offload_checkpointing` can save memory but cannot be combined with `--blocks_to_swap`; Chroma does not support it.
- Do not use `--v2`, `--v_parameterization`, `--clip_skip`, or SD1/2 `--max_token_length`; use `--t5xxl_max_token_length` instead.

## Chroma

- Use `flux_train_network.py --model_type chroma`.
- Chroma uses the FLUX training path but does not use CLIP-L; omit `--clip_l`.
- T5XXL and AE assets are the same style as FLUX.
- Add `--guidance_scale 0.0` because Chroma is not distilled the same way as FLUX.1 dev.
- Add `--apply_t5_attn_mask`; Chroma requires T5 attention masks.
- `--timestep_sampling sigmoid` is recommended for Chroma.

## Lumina 2

- Use `lumina_train_network.py`.
- Required family assets include the Lumina model, `--gemma2`, and `--ae`.
- Uses Gemma2 text encoder strategies and a Lumina latents caching strategy.
- `--cache_text_encoder_outputs` is useful when not training Gemma2. If training the text encoder, avoid cached text encoder outputs.
- `--fp8_base` and `--blocks_to_swap` can reduce memory depending on hardware and checkpoint format.
- Native parser tests cover trainer methods for loading Lumina model, Gemma2, AE, caching, scheduler, metadata, and text-encoder training decisions.

## HunyuanImage

- Use `hunyuan_image_train_network.py`.
- The script has Hunyuan-specific DiT, VAE, and text encoder handling.
- Prefer `--fp8_scaled`; `--fp8_base` and `--fp8_base_unet` are not supported and are ignored when `--fp8_scaled` is used.
- `--fp8_vl` is for VLM text encoder fp8.
- `--attn_mode` can select among `torch`, `xformers`, `flash`, `sageattn`, and `sdpa`; `sageattn` is inference-only and not for training.
- `--xformers` may require `--split_attn` in this family.
- `--cache_text_encoder_outputs` and block swapping are available for memory control.

## Anima

- Use `anima_train_network.py`.
- Anima does not support `--fp8_base`, `--fp8_base_unet`, or scaled fp8 in the current trainer path.
- `--compile` applies per-block `torch.compile` through the Anima trainer.
- Do not combine `--compile` with accelerate `--torch_compile`.
- Do not combine `--compile_fullgraph` with `--split_attn`, because split attention uses dynamic control flow.
- `--blocks_to_swap` conflicts with `--cpu_offload_checkpointing`; it also conflicts with unsloth offload checkpointing.
- LoHa/LoKr support includes Anima-specific module targeting defaults; `networks.loha` and `networks.lokr` can be used when the environment has required dependencies.

## LECO

- Use `train_leco.py` for SD1/2 and `sdxl_train_leco.py` for SDXL.
- `--prompts_file` is required.
- Network defaults are LoRA-like: `--network_module networks.lora`, `--network_dim 4`, `--network_alpha 1.0`.
- Native tests verify parser setup, shared training argument validation, and deepspeed plugin preparation for both SD and SDXL LECO scripts.

## ControlNet-LLLite

- Use `sdxl_train_control_net_lllite.py` only; current docs describe SDXL support.
- Dataset subsets need `conditioning_data_dir`; conditioning images must share basenames with training images.
- Random crop cannot be used.
- `--network_module` is not required; set `--cond_emb_dim` for conditioning image embedding dimension and `--network_dim` for LoRA-like module rank.
- Memory use is high. Use caching, gradient checkpointing, bf16/full bf16 when hardware supports it, and conservative batch sizes.

## Inpainting

- Add `--train_inpainting` to supported training scripts.
- The UNet uses 9-channel input: noisy latents, downsampled mask, and masked-image latents.
- With normal checkpoints, the input layer is expanded from 4 to 9 channels automatically; inpainting checkpoints are detected automatically.
- Do not combine `--train_inpainting` with `--cache_latents` or `--cache_latents_to_disk`.
- `--alpha_mask` is loss weighting from source image alpha; it is not the same as `--train_inpainting`.

## Validation

- Validation can be configured in dataset TOML with per-subset `validation_split`; route TOML authoring to `../data-preparation`.
- CLI `--validation_split` applies globally and is ignored where TOML subset validation splits exist.
- `--validate_every_n_steps`, `--validate_every_n_epochs`, `--max_validation_steps`, and `--validation_seed` control cadence, cost, and determinism.
- Track `loss/validation` in the configured logger.

## Network Modules

- `networks.lora`: standard LoRA for SD/SDXL/SD3 and other supported families.
- `networks.lora_flux`: FLUX/Chroma LoRA path.
- `networks.loha`: LoHa/LyCORIS-style low-rank Hadamard product.
- `networks.lokr`: LoKr/LyCORIS-style Kronecker product.
- Invalid or missing modules fail at import time. Check spelling and installed package context before blaming model paths.

## Memory Option Ladder

Use this order before changing training goals:

1. Reduce dataset batch size and resolution where appropriate.
2. Enable `--gradient_checkpointing`.
3. Use `--mixed_precision bf16` or `fp16` compatible with hardware.
4. Use family-compatible attention: `--sdpa` for PyTorch SDPA or `--xformers` only when xformers is installed and compatible.
5. Cache latents where compatible; do not cache latents for inpainting training.
6. Cache text encoder outputs when text encoders are frozen.
7. Use family fp8 options only where supported.
8. Use `--blocks_to_swap`; expect slower training.
9. Switch optimizer from memory-heavy AdamW to 8-bit AdamW, Adafactor, Prodigy, or another available optimizer.
