# Dataset Layouts and Launch Workflow

Use this reference to prepare local datasets and convert user intent into safe `accelerate launch` commands.

## Local Imagefolder Basics

Diffusers training scripts commonly accept either a Hub dataset id via `--dataset_name` or a local image folder via `--train_data_dir`/`--instance_data_dir`. A minimal local imagefolder can be:

```text
data/
  0001.png
  0002.jpg
  0003.webp
```

For captioned text-to-image datasets, include a metadata file that maps images to text. Common `datasets` imagefolder metadata names are `metadata.jsonl`, `metadata.csv`, or `metadata.json`. A JSON Lines file can look like:

```jsonl
{"file_name":"0001.png","text":"a watercolor robot"}
{"file_name":"0002.jpg","text":"a ceramic fox on a shelf"}
```

The bundled validator checks that files exist and caption fields are non-empty:

```bash
python sub-skills/training-recipes/scripts/dataset_layout_check.py --data-dir data --require-captions
```

## DreamBooth Datasets

DreamBooth and DreamBooth LoRA normally use an `--instance_data_dir` with a small set of subject/style images and a single `--instance_prompt`. Captions are optional unless the chosen script or user customization expects them. If using prior preservation, also prepare a class-image folder for `--class_data_dir` or let the script generate class images when supported.

Checklist:
- 3-30 good instance images for a subject is typical; more may be needed for styles.
- Avoid near-duplicates and low-quality images.
- Choose a unique token in `--instance_prompt`.
- Use LoRA first when the user wants a lightweight adapter.

## Text-to-Image Captioned Data

Text-to-image training expects an image column and a caption column. For local imagefolder, verify metadata before launch and pass `--caption_column` only if the column is not the script default. For Hub datasets, inspect or ask for column names before composing a command.

Checklist:
- Every training image has a caption.
- Captions are descriptive enough for the target task.
- Image sizes and aspect ratios are acceptable for the script's resize/crop settings.
- If the user wants offline/local-only behavior, pass local model and dataset paths and avoid commands that contact the Hub.

## Control and Adapter Data

ControlNet, Flux control, and T2I-Adapter datasets usually need aligned target images, conditioning images, and prompts. A Hub dataset often has columns like `image`, `conditioning_image`, and `text`. For local paired folders, require the same stem or file order and validate counts:

```bash
python sub-skills/training-recipes/scripts/dataset_layout_check.py \
  --data-dir images \
  --conditioning-dir conditioning \
  --require-captions
```

For JSONL-based Flux control training, rows commonly contain `image`, `text`, and `conditioning_image`. Validate that referenced files exist before suggesting a launch.

## Accelerate Launch Pattern

Use this structure when composing commands:

```bash
accelerate launch --mixed_precision="fp16" SCRIPT.py \
  --pretrained_model_name_or_path="MODEL" \
  --train_data_dir="DATA" \
  --resolution=512 \
  --train_batch_size=1 \
  --gradient_accumulation_steps=4 \
  --gradient_checkpointing \
  --checkpointing_steps=500 \
  --max_train_steps=1000 \
  --output_dir="OUT"
```

Use `bf16` only when hardware supports it and the recipe recommends it. Use `fp16` for many SD 1.x/SDXL GPU runs. Do not use mixed precision blindly on CPU-only environments.

## Command Builder

The bundled command builder prints safe command templates for common recipes and refuses expensive defaults unless `--confirm-expensive-run` is supplied:

```bash
python sub-skills/training-recipes/scripts/training_command_builder.py \
  --recipe dreambooth-lora \
  --model stable-diffusion-v1-5/stable-diffusion-v1-5 \
  --dataset ./dog \
  --output-dir ./out/dog-lora \
  --instance-prompt "a photo of sks dog"
```

Supported recipe ids include `dreambooth-lora`, `dreambooth-lora-sdxl`, `dreambooth-lora-flux`, `text-to-image`, `text-to-image-lora`, `text-to-image-sdxl`, `textual-inversion`, `controlnet`, `controlnet-sdxl`, `controlnet-sd3`, `controlnet-flux`, `t2i-adapter-sdxl`, `instruct-pix2pix`, and `flux-control-lora`.

## Safe Smoke Tests

A smoke test can catch import, model-path, dataset-column, and device errors without committing to a long run, but it still may download models or allocate GPUs. Only propose it after confirmation:

- Add `--max_train_steps=1`.
- Use a tiny dataset subset when the script supports `--max_train_samples`.
- Disable Hub push and remote tracking.
- Use a throwaway `--output_dir`.
- Keep validation off unless the user specifically wants to test validation image/prompt plumbing.
