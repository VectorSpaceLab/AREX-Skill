# Training Command Templates

These templates are distilled from sd-scripts training docs and root training scripts. Replace placeholder paths before use. Full training normally requires model weights, data, accelerator configuration, and a compatible GPU stack.

## Common Command Skeleton

```bash
accelerate launch --num_cpu_threads_per_process 1 SCRIPT.py \
  --pretrained_model_name_or_path path/to/base_model.safetensors \
  --dataset_config path/to/dataset.toml \
  --output_dir path/to/output \
  --output_name run_name \
  --save_model_as safetensors \
  --max_train_epochs 10 \
  --save_every_n_epochs 1 \
  --mixed_precision bf16 \
  --optimizer_type AdamW8bit \
  --learning_rate 1e-4 \
  --gradient_checkpointing
```

Prefer `bf16` on Ampere-or-newer GPUs that support it; otherwise use `fp16`. `AdamW8bit` requires bitsandbytes. If bitsandbytes is unavailable, use `AdamW`, `Adafactor`, or another installed optimizer.

## SD1/SD2 LoRA

```bash
accelerate launch --num_cpu_threads_per_process 1 train_network.py \
  --pretrained_model_name_or_path path/to/sd15_or_sd2.safetensors \
  --dataset_config path/to/dataset.toml \
  --output_dir output \
  --output_name my_lora \
  --save_model_as safetensors \
  --network_module networks.lora \
  --network_dim 32 \
  --network_alpha 16 \
  --learning_rate 1e-4 \
  --optimizer_type AdamW8bit \
  --mixed_precision bf16 \
  --cache_latents \
  --gradient_checkpointing \
  --xformers
```

For SD2 v-prediction checkpoints, add both `--v2` and `--v_parameterization`. Do not add them for SD1 or newer DiT-family models.

## SDXL LoRA

```bash
accelerate launch --num_cpu_threads_per_process 1 sdxl_train_network.py \
  --pretrained_model_name_or_path path/to/sdxl_base.safetensors \
  --dataset_config path/to/sdxl_dataset.toml \
  --output_dir output \
  --output_name my_sdxl_lora \
  --save_model_as safetensors \
  --network_module networks.lora \
  --network_dim 32 \
  --network_alpha 16 \
  --learning_rate 1e-4 \
  --optimizer_type AdamW8bit \
  --mixed_precision bf16 \
  --cache_latents \
  --cache_text_encoder_outputs \
  --gradient_checkpointing \
  --xformers
```

`--cache_text_encoder_outputs` reduces VRAM and speeds training but disables caption augmentations such as shuffle/dropout because text encoder outputs are precomputed.

## LoHa and LoKr

Use the same family-specific script as LoRA and change `--network_module`:

```bash
--network_module networks.loha --network_dim 32 --network_alpha 16
```

```bash
--network_module networks.lokr --network_dim 32 --network_alpha 16
```

For SDXL/Anima conv layers, optional network args include:

```bash
--network_args "conv_dim=16" "conv_alpha=8" "use_tucker=True"
```

For dropout and module targeting:

```bash
--network_args "rank_dropout=0.1" "module_dropout=0.1" "verbose=True"
```

## SD3/SD3.5 LoRA

```bash
accelerate launch --num_cpu_threads_per_process 1 sd3_train_network.py \
  --pretrained_model_name_or_path path/to/sd3_or_sd35.safetensors \
  --clip_l path/to/clip_l.safetensors \
  --clip_g path/to/clip_g.safetensors \
  --t5xxl path/to/t5xxl.safetensors \
  --dataset_config path/to/sd3_dataset.toml \
  --output_dir output \
  --output_name my_sd3_lora \
  --save_model_as safetensors \
  --network_module networks.lora \
  --network_dim 32 \
  --network_alpha 16 \
  --learning_rate 1e-4 \
  --optimizer_type AdamW8bit \
  --mixed_precision bf16 \
  --sdpa \
  --cache_text_encoder_outputs \
  --gradient_checkpointing \
  --blocks_to_swap 16
```

If the SD3 checkpoint is a single file with embedded components, separate `--clip_l`, `--clip_g`, `--t5xxl`, or `--vae` paths may be unnecessary. `--v2`, `--v_parameterization`, and `--clip_skip` are not SD3 options.

## FLUX.1 LoRA

```bash
accelerate launch --num_cpu_threads_per_process 1 flux_train_network.py \
  --pretrained_model_name_or_path path/to/flux1-dev.safetensors \
  --clip_l path/to/clip_l.safetensors \
  --t5xxl path/to/t5xxl_fp16.safetensors \
  --ae path/to/ae.safetensors \
  --dataset_config path/to/flux_dataset.toml \
  --output_dir output \
  --output_name my_flux_lora \
  --save_model_as safetensors \
  --network_module networks.lora_flux \
  --network_dim 32 \
  --network_alpha 16 \
  --learning_rate 1e-4 \
  --optimizer_type AdamW8bit \
  --mixed_precision bf16 \
  --sdpa \
  --fp8_base \
  --guidance_scale 1.0 \
  --timestep_sampling flux_shift \
  --model_prediction_type raw \
  --cache_text_encoder_outputs \
  --gradient_checkpointing \
  --blocks_to_swap 18
```

To train T5XXL LoRA too, omit `--network_train_unet_only` and add `--network_args "train_t5xxl=True"`; then do not use `--cache_text_encoder_outputs` if T5XXL is trainable.

## Chroma LoRA

```bash
accelerate launch --num_cpu_threads_per_process 1 flux_train_network.py \
  --model_type chroma \
  --pretrained_model_name_or_path path/to/Chroma.safetensors \
  --t5xxl path/to/t5xxl_fp16.safetensors \
  --ae path/to/ae.safetensors \
  --dataset_config path/to/chroma_dataset.toml \
  --output_dir output \
  --output_name my_chroma_lora \
  --save_model_as safetensors \
  --network_module networks.lora_flux \
  --network_dim 32 \
  --network_alpha 16 \
  --learning_rate 1e-4 \
  --optimizer_type AdamW8bit \
  --mixed_precision bf16 \
  --sdpa \
  --fp8_base \
  --guidance_scale 0.0 \
  --timestep_sampling sigmoid \
  --model_prediction_type raw \
  --apply_t5_attn_mask \
  --cache_text_encoder_outputs \
  --gradient_checkpointing
```

Chroma does not use CLIP-L; omit `--clip_l`. `--guidance_scale 0.0` and `--apply_t5_attn_mask` are required/recommended Chroma differences.

## Lumina 2 LoRA

```bash
accelerate launch --num_cpu_threads_per_process 1 lumina_train_network.py \
  --pretrained_model_name_or_path path/to/lumina2_model.safetensors \
  --gemma2 path/to/gemma2 \
  --ae path/to/ae.safetensors \
  --dataset_config path/to/lumina_dataset.toml \
  --output_dir output \
  --output_name my_lumina_lora \
  --save_model_as safetensors \
  --network_module networks.lora \
  --network_dim 32 \
  --network_alpha 16 \
  --learning_rate 1e-4 \
  --optimizer_type AdamW8bit \
  --mixed_precision bf16 \
  --fp8_base \
  --cache_text_encoder_outputs \
  --gradient_checkpointing \
  --blocks_to_swap 8
```

`--gemma2` and `--ae` are family-specific required assets. Cache text encoder outputs unless the command intentionally trains Gemma2.

## HunyuanImage LoRA

```bash
accelerate launch --num_cpu_threads_per_process 1 hunyuan_image_train_network.py \
  --pretrained_model_name_or_path path/to/hunyuan_image_dit.safetensors \
  --vae path/to/hunyuan_vae.safetensors \
  --dataset_config path/to/hunyuan_dataset.toml \
  --output_dir output \
  --output_name my_hunyuan_lora \
  --save_model_as safetensors \
  --network_module networks.lora \
  --network_dim 32 \
  --network_alpha 16 \
  --learning_rate 1e-4 \
  --optimizer_type AdamW8bit \
  --mixed_precision bf16 \
  --fp8_scaled \
  --cache_text_encoder_outputs \
  --gradient_checkpointing \
  --blocks_to_swap 8
```

Use `--fp8_scaled` for HunyuanImage; `--fp8_base` and `--fp8_base_unet` are ignored or unsupported in this script.

## Anima LoRA with Optional Compile

```bash
accelerate launch --num_cpu_threads_per_process 1 anima_train_network.py \
  --pretrained_model_name_or_path path/to/anima_dit.safetensors \
  --dataset_config path/to/anima_dataset.toml \
  --output_dir output \
  --output_name my_anima_lora \
  --save_model_as safetensors \
  --network_module networks.lora \
  --network_dim 32 \
  --network_alpha 16 \
  --learning_rate 1e-4 \
  --optimizer_type AdamW8bit \
  --mixed_precision bf16 \
  --cache_text_encoder_outputs \
  --gradient_checkpointing \
  --compile
```

`--compile` applies per-block `torch.compile` in the Anima trainer. Do not combine `--compile` with `--torch_compile`; do not use `--compile_fullgraph` with `--split_attn`. Anima does not support `--fp8_base` or `--fp8_base_unet`.

## DreamBooth / Native Fine-Tuning

```bash
accelerate launch --num_cpu_threads_per_process 1 train_db.py \
  --pretrained_model_name_or_path path/to/base_model.safetensors \
  --train_data_dir path/to/dreambooth_images \
  --reg_data_dir path/to/regularization_images \
  --output_dir output \
  --output_name my_db_model \
  --save_model_as safetensors \
  --resolution 512,512 \
  --train_batch_size 1 \
  --learning_rate 1e-6 \
  --max_train_epochs 10 \
  --mixed_precision bf16 \
  --cache_latents \
  --gradient_checkpointing \
  --xformers
```

For caption/metadata-driven full fine-tuning, use `fine_tune.py` with equivalent model, output, optimizer, precision, and dataset/caption arguments.

## Textual Inversion

```bash
accelerate launch --num_cpu_threads_per_process 1 train_textual_inversion.py \
  --pretrained_model_name_or_path path/to/base_model.safetensors \
  --train_data_dir path/to/images \
  --output_dir output \
  --output_name my_embedding \
  --token_string "<my-token>" \
  --init_word "style" \
  --num_vectors_per_token 4 \
  --resolution 512,512 \
  --train_batch_size 1 \
  --learning_rate 5e-4 \
  --max_train_epochs 10 \
  --mixed_precision bf16 \
  --cache_latents \
  --gradient_checkpointing
```

## LECO Slider

```bash
accelerate launch --num_cpu_threads_per_process 1 train_leco.py \
  --pretrained_model_name_or_path path/to/sd_model.safetensors \
  --prompts_file path/to/slider.yaml \
  --output_dir output \
  --output_name my_leco_slider \
  --save_model_as safetensors \
  --network_module networks.lora \
  --network_dim 4 \
  --network_alpha 1 \
  --learning_rate 1e-4 \
  --max_train_steps 1000 \
  --mixed_precision bf16 \
  --xformers
```

For SDXL slider training, use `sdxl_train_leco.py` with an SDXL base model. `--prompts_file` is required. The prompt file defines target/positive/negative or neutral settings, multipliers, and weights.

## SDXL ControlNet-LLLite

```bash
accelerate launch --num_cpu_threads_per_process 1 sdxl_train_control_net_lllite.py \
  --pretrained_model_name_or_path path/to/sdxl_base.safetensors \
  --dataset_config path/to/lllite_dataset.toml \
  --output_dir output \
  --output_name my_controlnet_lllite \
  --save_model_as safetensors \
  --network_dim 64 \
  --cond_emb_dim 32 \
  --learning_rate 2e-4 \
  --optimizer_type AdamW8bit \
  --mixed_precision bf16 \
  --full_bf16 \
  --cache_latents \
  --cache_latents_to_disk \
  --cache_text_encoder_outputs \
  --cache_text_encoder_outputs_to_disk \
  --gradient_checkpointing \
  --xformers
```

The dataset TOML subset must include `conditioning_data_dir` whose files share basenames with training images. Random crop is not supported for LLLite. This feature is SDXL-only and experimental.

## Inpainting Training

Add `--train_inpainting` to compatible training scripts such as `train_network.py`, `sdxl_train_network.py`, `train_db.py`, `fine_tune.py`, and `train_textual_inversion.py`.

Important: do not combine `--train_inpainting` with `--cache_latents` or `--cache_latents_to_disk`, because masks are generated randomly per step from source images.

For inpainting sample previews, each prompt line needs an `--i path/to/reference_image` directive. Lines without `--i` are skipped during inpainting sampling.

## Validation Loss

Prefer dataset TOML validation splits via the data-preparation sub-skill. CLI validation flags are:

```bash
--validation_split 0.1 \
--validate_every_n_epochs 1 \
--max_validation_steps 50 \
--validation_seed 42
```

If both TOML `validation_split` and CLI `--validation_split` are present, TOML subset settings take precedence. Validation logs the `loss/validation` metric to the configured tracker.

## Sampling During Training

Most network trainers share sample options such as:

```bash
--sample_prompts path/to/prompts.txt \
--sample_every_n_epochs 1
```

Use sample prompts for previews only. For inpainting training, include `--i` image references in the prompt file. For model-family-specific inference syntax or post-training generation, route to `../generation`.
