---
name: training
description: "Choose and compose sd-scripts training commands for
  LoRA/additional networks, DreamBooth/native fine-tuning, Textual Inversion,
  ControlNet-LLLite, LECO, validation loss, inpainting, and
  SD/SDXL/SD3/FLUX/Chroma/Lumina/HunyuanImage/Anima model-family training."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# sd-scripts Training

Use this sub-skill when the user needs a training command, training-option diagnosis, or model-family routing for sd-scripts. It is for composing commands and explaining constraints; do not run full training unless the user explicitly provides model weights, dataset paths, compute budget, and permission for GPU/long-running work.

## Route First

- Use `../data-preparation` for dataset TOML authoring, captioning, bucketing, repeats, subsets, and validation subset layout.
- Use this sub-skill for training script selection, flags, model-family requirements, validation-loss flags, inpainting flags, optimizer/memory choices, and command templates.
- Use `../model-utilities` for post-training merge, conversion, metadata inspection, checkpoint extraction, or LoRA application to checkpoints.
- Use `../generation` for inference-only image generation, sample prompt syntax for generation scripts, and post-training preview generation outside a training run.

## Safe Operating Rules

1. Build commands with placeholders first; do not execute training commands by default.
2. Prefer `accelerate launch --num_cpu_threads_per_process 1 <script>.py ...` for training scripts.
3. Require concrete paths for the base model, dataset config or training data, and output directory before suggesting a runnable command.
4. Match script and flags to the model family; SD1/2 flags such as `--v2`, `--v_parameterization`, `--clip_skip`, and `--max_token_length` do not apply to SD3/FLUX-family DiT scripts.
5. Call out expensive/full-training checks as GPU/weights-dependent and skip by default; help-only commands are safer but may still import heavy dependencies.

## Script Selection

| Goal | Script | Key additions |
|---|---|---|
| SD1/SD2 LoRA/additional network | `train_network.py` | `--network_module=networks.lora`; add `--v2 --v_parameterization` for SD2 v-prediction checkpoints only |
| SDXL LoRA/additional network | `sdxl_train_network.py` | SDXL checkpoint, `--cache_text_encoder_outputs`, often `--cache_latents`; no `--v2`/`--v_parameterization` |
| SD3/SD3.5 LoRA | `sd3_train_network.py` | MMDiT model plus optional `--clip_l`, `--clip_g`, `--t5xxl`, `--vae`; `--sdpa`, `--blocks_to_swap` |
| FLUX.1 LoRA | `flux_train_network.py` | `--clip_l`, `--t5xxl`, `--ae`, `--network_module=networks.lora_flux`, `--guidance_scale 1.0` |
| Chroma LoRA | `flux_train_network.py` | `--model_type=chroma`, omit `--clip_l`, add `--guidance_scale 0.0 --apply_t5_attn_mask` |
| Lumina 2 LoRA | `lumina_train_network.py` | Lumina DiT, `--gemma2`, `--ae`; cache text encoder outputs unless training Gemma2 |
| HunyuanImage LoRA | `hunyuan_image_train_network.py` | Hunyuan DiT/VAE/text encoders; prefer `--fp8_scaled` over unsupported `--fp8_base` |
| Anima LoRA/LoHa/LoKr | `anima_train_network.py` | Anima/Qwen Image components; optional `--compile` for per-block `torch.compile` |
| DreamBooth/native SD fine-tune | `train_db.py` | Directory-style DreamBooth dataset; trains base model weights |
| Fine-tune from metadata/caption files | `fine_tune.py` | Caption/metadata-driven full model fine-tuning |
| Textual Inversion | `train_textual_inversion.py` | Placeholder token initialization and embedding outputs |
| LECO slider | `train_leco.py` or `sdxl_train_leco.py` | `--prompts_file` is required; parser supports shared training validation |
| SDXL ControlNet-LLLite | `sdxl_train_control_net_lllite.py` | Dataset subset needs `conditioning_data_dir`; set `--cond_emb_dim` and `--network_dim` |

## Command Workflow

1. Identify model family and training kind.
2. Ask for or route to dataset config. For most LoRA/additional network jobs, prefer `--dataset_config path/to/dataset.toml`.
3. Select network module: `networks.lora`, `networks.lora_flux`, `networks.loha`, or `networks.lokr` as appropriate.
4. Add model-family assets: FLUX/Chroma need T5XXL and AE; SD3 may need separate CLIP-L/CLIP-G/T5XXL/VAE; Lumina needs Gemma2 and AE; HunyuanImage/Anima need their family-specific components.
5. Add memory settings conservatively: `--gradient_checkpointing`, `--mixed_precision bf16` or `fp16`, `--sdpa` or `--xformers`, `--cache_latents`, `--cache_text_encoder_outputs`, `--blocks_to_swap`, or family-specific fp8 options.
6. Add output/logging/checkpoint flags: `--output_dir`, `--output_name`, `--save_model_as safetensors`, `--save_every_n_epochs`, optional `--logging_dir`, `--log_with tensorboard` or `wandb`.
7. Add validation flags only when validation data exists: `--validation_split`, `--validate_every_n_steps`, `--validate_every_n_epochs`, `--max_validation_steps`, `--validation_seed`.
8. Include sample prompt flags only when the user wants training-time previews and has prompt files/images compatible with the task.

## References

- `references/commands.md`: ready-to-adapt command templates and option clusters.
- `references/model-family-guide.md`: model-family script requirements, incompatible flags, and memory notes.
- `references/troubleshooting.md`: common failure modes and targeted fixes.
- `scripts/build_training_command.py`: safe command-template assembler that prints shell commands without executing training.

## Use the Command Builder

Use the bundled builder when the user wants a starter command and has paths available. Run it from this sub-skill directory or with the path used by the host agent to access bundled skill scripts:

```bash
python scripts/build_training_command.py \
  --family flux --kind lora \
  --pretrained_model path/to/flux1-dev.safetensors \
  --dataset_config path/to/dataset.toml \
  --output_dir output --output_name my_flux_lora \
  --clip_l path/to/clip_l.safetensors \
  --t5xxl path/to/t5xxl_fp16.safetensors \
  --ae path/to/ae.safetensors
```

The script prints an `accelerate launch ...` command; it never starts training.
