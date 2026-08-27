# Training Recipe Selection

This reference summarizes Diffusers training recipe families and the command arguments a future agent should use when helping users compose or adapt training runs. This skill does not depend on the original repository checkout; use `../scripts/training_command_builder.py` to produce a safe argument plan, then map that plan onto a user-provided training entrypoint or a maintained project-local script.

## Common Setup

Training examples expect Diffusers installed with training dependencies: `accelerate`, `datasets`, `protobuf`, `tensorboard`, `Jinja2`, `peft`, and `timm`. Some recipes additionally need example-specific requirements such as `bitsandbytes`, `transformers`, `torchvision`, `wandb`, image preprocessing packages, or gated model access.

Before a launch command:
- Run `accelerate config` or `accelerate config default` once for the environment.
- Prefer `accelerate launch SCRIPT.py ...` over direct `python SCRIPT.py` for training.
- Use `--checkpointing_steps` and a unique `--output_dir` so interrupted runs can resume with `--resume_from_checkpoint`.
- Add `--validation_prompt`/`--validation_image` only when the script supports them and the user wants intermediate qualitative checks.
- Do not add `--push_to_hub`, `--hub_token`, or `--report_to=wandb` unless the user explicitly asks.

## DreamBooth and DreamBooth LoRA

Use for a subject/style with a small image set and an `--instance_prompt` containing a unique token such as `sks dog`.

Recipe families:
- Full-model DreamBooth for heavier subject/style specialization.
- SD 1.x/2.x LoRA DreamBooth for lightweight adapter training.
- SDXL LoRA DreamBooth for SDXL-specific two-encoder behavior.
- SD3 DreamBooth/LoRA for SD3 checkpoints and dependencies.
- Flux DreamBooth/LoRA for high-memory Flux workflows.

Core arguments:
- `--pretrained_model_name_or_path MODEL`
- `--instance_data_dir IMAGE_DIR`
- `--instance_prompt "a photo of TOKEN class"`
- `--output_dir OUT`
- `--resolution 512` for SD 1.x/2.x; use recipe docs and hardware for SDXL/Flux/SD3.
- `--train_batch_size 1`, `--gradient_accumulation_steps N`, `--learning_rate`, `--max_train_steps`.

Prior preservation adds `--with_prior_preservation`, `--class_data_dir`, `--class_prompt`, `--num_class_images`, and `--prior_loss_weight`. Warn that DreamBooth overfits easily and full DreamBooth is much heavier than LoRA.

## Text-to-Image and Text-to-Image LoRA

Use when the user has image-caption pairs or a Hugging Face dataset and wants to fine-tune a generative model on a broader concept distribution.

Recipe families:
- Full text-to-image fine-tuning.
- Text-to-image LoRA fine-tuning.
- SDXL text-to-image fine-tuning.
- SDXL text-to-image LoRA fine-tuning.

Core arguments:
- `--pretrained_model_name_or_path MODEL`
- `--dataset_name DATASET_ID` or `--train_data_dir LOCAL_DIR`
- `--image_column image` and `--caption_column text` when column names differ.
- `--resolution`, `--center_crop`, `--random_flip`, `--train_batch_size`, `--gradient_accumulation_steps`, `--learning_rate`, `--lr_scheduler`, `--lr_warmup_steps`, `--max_train_steps`, `--output_dir`.

LoRA adds `--rank`; SDXL variants may support `--pretrained_vae_model_name_or_path`, `--proportion_empty_prompts`, and timestep-bias flags. SDXL loads two tokenizers/text encoders and can precompute prompt and VAE embeddings, so memory usage can spike before the training loop.

## Textual Inversion

Use when the user wants to learn a new token embedding rather than tune UNet/adapter weights.

Recipe families:
- SD 1.x/2.x textual inversion.
- SDXL textual inversion.

Core arguments:
- `--pretrained_model_name_or_path MODEL`
- `--train_data_dir IMAGE_DIR`
- `--placeholder_token "<token>"`
- `--initializer_token "class"`
- `--learnable_property object|style`
- `--resolution`, `--train_batch_size`, `--gradient_accumulation_steps`, `--max_train_steps`, `--learning_rate`, `--output_dir`.

Textual inversion outputs learned embeddings and is usually lighter than LoRA, but token choice matters. Pick a placeholder token that does not already tokenize into a common word.

## ControlNet, T2I-Adapter, and InstructPix2Pix

Use adapter/control recipes when each training example contains a prompt plus one or more conditioning inputs.

Control and editing recipe families:
- ControlNet for SD 1.x/2.x, SDXL, SD3, and Flux.
- T2I-Adapter for SDXL adapter training.
- InstructPix2Pix for image-editing datasets.

Core adapter arguments:
- `--pretrained_model_name_or_path MODEL`
- `--dataset_name DATASET_ID` or a local format supported by the script.
- `--image_column`, `--conditioning_image_column`, and `--caption_column` for ControlNet/T2I-Adapter datasets.
- `--original_image_column`, `--edited_image_column`, and `--edit_prompt_column` for InstructPix2Pix if column names differ.
- `--output_dir`, `--resolution`, `--learning_rate`, `--train_batch_size`, `--gradient_accumulation_steps`, `--max_train_steps`.

ControlNet can initialize from a pretrained ControlNet with `--controlnet_model_name_or_path` or from a UNet when omitted. Default full ControlNet training is memory-heavy; use LoRA/control variants or smaller runs when possible.

## SDXL vs Flux vs SD3 Safety Choices

Choose SDXL when the user needs the SDXL ecosystem and can handle higher memory than SD 1.x. Use `--pretrained_vae_model_name_or_path` if the recipe recommends an fp16-safe VAE, and expect two-tokenizer/two-encoder behavior.

Choose Flux only when the user explicitly targets Flux, accepts gated-model requirements, and has high-memory hardware. Flux ControlNet examples report A100-class memory use, bf16, CPU offload, and precomputed embeddings as common constraints. Do not present Flux training as a casual consumer-GPU run.

Choose SD3 only when the user targets SD3-specific checkpoints/scripts. Use SD3-specific example requirements and arguments; do not substitute SDXL script names.

## Expensive-Run Guardrails

A future agent should not start training automatically. For real launches:
- Confirm hardware, expected duration, disk space, output path, and whether the model is gated/private.
- Start with a smoke run such as `--max_train_steps 1` only if the user agrees and data/model access is safe.
- Keep `--output_dir` unique and avoid deleting previous checkpoints.
- Avoid `--push_to_hub` and experiment tracking unless requested.
