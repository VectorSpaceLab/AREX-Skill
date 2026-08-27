# Training Troubleshooting

Use this guide when Diffusers training commands fail before or during launch.

## Optional Dependency and Import Failures

Symptoms:
- `ModuleNotFoundError: accelerate`, `datasets`, `peft`, `timm`, `tensorboard`, or `bitsandbytes`.
- Example script imports a class that is absent from the installed Diffusers version.
- `accelerate: command not found`.

Actions:
- Install Diffusers with training extras for the project environment: `pip install -e .[training]` or install the equivalent package extras in the user's environment.
- Install the example-specific requirements file for the selected recipe, such as SDXL, SD3, Flux, or ControlNet requirements.
- Re-run `accelerate config default` if Accelerate has no config.
- If an example script is from a newer checkout than the installed package, reinstall the local package from the same checkout.

## Backend, Device, and Dtype Mistakes

Symptoms:
- CUDA out of memory, bf16 unsupported, xFormers import errors, or bitsandbytes failing on CPU/unsupported GPU.
- Mixed precision passed on a CPU-only machine.
- Flux/SDXL/SD3 recipe hangs or OOMs during model loading or embedding precompute.

Actions:
- Ask for hardware and `torch.cuda.is_available()` before recommending full runs.
- Use `--train_batch_size=1`, increase `--gradient_accumulation_steps`, add `--gradient_checkpointing`, reduce `--resolution`, and set conservative `--max_train_steps`.
- Use `--mixed_precision="fp16"` for many CUDA SD runs; use `bf16` only on supported hardware and when the recipe recommends it.
- Do not add `--use_8bit_adam` unless `bitsandbytes` is installed and supported.
- For Flux control training, warn that the examples are A100-class/high-memory recipes; prefer LoRA/control LoRA and explicit confirmation.

## Local, Offline, and Gated Model Problems

Symptoms:
- `Repository Not Found`, `401 Unauthorized`, gated model errors, SSL/network failures, or accidental Hub downloads in offline work.
- Local model path missing subfolders like `unet`, `vae`, `scheduler`, `tokenizer`, or SDXL `tokenizer_2`/`text_encoder_2`.

Actions:
- For gated models, ask the user to accept the model terms and authenticate with `hf auth login`; do not request or expose tokens.
- For offline mode, use local paths for `--pretrained_model_name_or_path`, datasets, VAE, ControlNet, and tokenizers; avoid `--push_to_hub`.
- Verify that local paths exist and match the expected model family before composing the final command.

## Dataset and Column Errors

Symptoms:
- `KeyError: image`, `caption`, `conditioning_image`, `text`, `edit_prompt`, or similar.
- Imagefolder loads but captions are empty or mismatched.
- ControlNet/T2I-Adapter conditioning images do not align with target images.

Actions:
- Run `dataset_layout_check.py` on local folders before launch.
- Ask for dataset column names or inspect a small sample when the user uses a Hub dataset.
- Pass explicit `--image_column`, `--caption_column`, `--conditioning_image_column`, `--original_image_column`, `--edited_image_column`, or `--edit_prompt_column` when defaults do not match.
- For DreamBooth, remember that `--instance_data_dir` plus a single `--instance_prompt` is normal; do not force captions unless the selected script requires them.

## API Misuse and Recipe Mismatch

Symptoms:
- Passing `--instance_prompt` to text-to-image scripts.
- Passing `--train_data_dir` where a DreamBooth script expects `--instance_data_dir`.
- Using SDXL arguments on SD 1.x scripts or Flux arguments on standard ControlNet scripts.

Actions:
- Match the script to the recipe and model family first, then add arguments.
- For SDXL, expect SDXL-specific scripts and optional `--pretrained_vae_model_name_or_path`.
- For SD3 and Flux, use only SD3/Flux example scripts and requirements.
- Generate a command with `training_command_builder.py` to catch missing required fields before handing it to the user.

## Workflow-Specific Failures

DreamBooth:
- Overfitting and identity drift are common. Suggest LoRA, fewer steps, prior preservation, and validation prompts.
- `--train_text_encoder` improves some cases but materially increases memory.

LoRA:
- Too high a rank or learning rate can overfit. Start with modest `--rank` and validate outputs.
- Ensure final usage loads LoRA weights rather than expecting a full pipeline directory unless the script saves a full model.

Textual inversion:
- Placeholder token already exists or tokenizes poorly. Choose a rare placeholder token and a suitable initializer token.
- Output is an embedding, not a full model.

ControlNet/T2I-Adapter:
- Conditioning images must be aligned to target images and transformed consistently.
- Validation requires both validation prompt and validation conditioning image when the script supports validation.

InstructPix2Pix:
- Dataset must contain original image, edited image, and edit instruction columns.
- Do not confuse image editing training with plain text-to-image caption training.

## Before Retrying

Before asking the user to rerun an expensive command:
- Show the exact changed arguments.
- Confirm expected downloads, GPU memory, disk writes, and output directory behavior.
- Prefer a one-step smoke run if the user wants validation and the environment can safely run it.
