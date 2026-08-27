# CLI reference

This is a condensed reference for the training entry points. The important flags fall into a few groups.

## Required inputs

- `--pretrained_model_name_or_path` — required base model id or local path.
- `--instance_data_dir` — required for single-concept runs.
- `--instance_prompt` — required for single-concept runs.
- `--concepts_list` — JSON list of concept objects; overrides the single-concept fields when present.
- `--output_dir` — defaults to `custom-diffusion-model`.

## Prior preservation

- `--with_prior_preservation` — enable class-image regularization.
- `--real_prior` — use retrieved class images rather than generated ones.
- `--class_data_dir` — class image directory for generated prior, or concept-specific bundle path when using real prior.
- `--class_prompt` — class prompt string for generated prior, or real-prior retrieval query / caption source depending on the route.
- `--num_class_images` — minimum class images to keep or synthesize; defaults to `100` in the source training entry points.
- `--prior_loss_weight` — prior-loss multiplier; defaults to `1.0`.
- `--prior_generation_precision` — precision used when the training route synthesizes class images locally.

## Data augmentation and sampling

- `--center_crop` — crop before resize when you want deterministic center framing.
- `--hflip` — apply horizontal flip augmentation.
- `--sample_batch_size` — batch size used when the route synthesizes class images locally.

## Optimization and memory

- `--freeze_model` — defaults to `crossattn_kv`; use `crossattn` for full cross-attention tuning.
- `--modifier_token` — plus-separated learned token strings.
- `--initializer_token` — plus-separated initializer tokens; must cover every modifier token.
- `--train_text_encoder` — enable text-encoder fine-tuning.
- `--learning_rate` — defaults to `1e-5`.
- `--train_batch_size` — per-device batch size.
- `--gradient_accumulation_steps` — accumulation factor before optimizer steps.
- `--gradient_checkpointing` — reduce memory at the cost of slower backward passes.
- `--use_8bit_adam` — requires bitsandbytes.
- `--enable_xformers_memory_efficient_attention` — requires xformers.
- `--mixed_precision` — `no`, `fp16`, or `bf16`.
- `--allow_tf32` — use TF32 on Ampere GPUs.
- `--scale_lr` — scale the learning rate by batch size and process count.

## Logging, validation, and checkpoints

- `--validation_prompt` — prompt used for validation images.
- `--num_validation_images` — number of validation images to generate.
- `--num_train_epochs` — training epochs when `--max_train_steps` is not used.
- `--max_train_steps` — total training steps; overrides epoch-based control.
- `--save_steps` / `--checkpointing_steps` — checkpoint cadence, depending on the route.
- `--checkpoints_total_limit` — retain only the newest checkpoints in the SDXL route.
- `--resume_from_checkpoint` — resume from `latest` or a named checkpoint in the SDXL route.
- `--logging_dir` — TensorBoard or tracker output folder.
- `--report_to` — tracker backend such as `tensorboard`, `wandb`, or `comet_ml`.

## SDXL-specific inputs

- `--pretrained_vae_model_name_or_path` — optional VAE override.
- `--resolution` — defaults to `1024` in the SDXL route.
- `--crops_coords_top_left_h` / `--crops_coords_top_left_w` — crop coordinate ids for SDXL.

## Hub integration

- `--push_to_hub` — enable Hub synchronization.
- `--hub_token` — token used for the Hub push.
- `--hub_model_id` — explicit repository id when you do not want the output directory name.

## Practical dependency notes

- `xformers`, `bitsandbytes`, `deepspeed`, and `modelcards` are optional extras.
- `accelerate` must already be configured for the backend you want to use.
- The route expects a CUDA-capable runtime for real training runs.
