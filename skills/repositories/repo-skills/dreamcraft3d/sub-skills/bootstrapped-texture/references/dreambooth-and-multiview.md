# DreamBooth and Multiview Texture Boosting

## Purpose

Read this when the user wants to mitigate multiview inconsistency or the Janus problem with the optional DreamCraft3D texture-boosting branch.

## When the optional branch is appropriate

Use the optional branch when:

- early coarse geometry is usable but rendered views show duplicated fronts, inconsistent backs, or unstable identity,
- the user can inspect generated multiview images before training a custom prior,
- GPU time, local model cache/downloads, and storage for LoRA checkpoints are acceptable.

Do not use it as a default replacement for the four canonical stages.

## Source workflow distilled

### 1. Generate multiview images from a reference image

The repository's multiview helper loads `sudo-ai/zero123plus-v1.1` with `local_files_only=True` and an optional Stable Diffusion x4 upscaler. It copies the input image to the save folder and crops the 2x3 grid result into `cropped_0.jpg` through `cropped_5.jpg`.

Source command shape:

```bash
python threestudio/scripts/img_to_mv.py \
  --image_path "load/images/mushroom_log_rgba.png" \
  --save_path ".cache/temp" \
  --prompt "a photo of mushroom" \
  --superres
```

Important adaptation notes:

- The source code moves models to `cuda:1`. If the host has only one visible GPU or a scheduler remaps devices, adapt the device before running or use `CUDA_VISIBLE_DEVICES` carefully.
- `local_files_only=True` means the model must already be present in the local Hugging Face cache path used by the script.
- Inspect the six cropped images manually or with a lightweight image grid before training DreamBooth. Bad multiview images can worsen texture consistency.

### 2. Train a personalized DeepFloyd DreamBooth LoRA

The README uses DeepFloyd IF and an instance prompt with a rare token:

```bash
export MODEL_NAME="DeepFloyd/IF-I-XL-v1.0"
export INSTANCE_DIR=".cache/temp"
export OUTPUT_DIR=".cache/if_dreambooth_mushroom"

accelerate launch threestudio/scripts/train_dreambooth_lora.py \
  --pretrained_model_name_or_path="$MODEL_NAME" \
  --instance_data_dir="$INSTANCE_DIR" \
  --output_dir="$OUTPUT_DIR" \
  --instance_prompt="a sks mushroom" \
  --resolution=64 \
  --train_batch_size=4 \
  --gradient_accumulation_steps=1 \
  --learning_rate=5e-6 \
  --scale_lr \
  --max_train_steps=1200 \
  --checkpointing_steps=600 \
  --pre_compute_text_embeddings \
  --tokenizer_max_length=77 \
  --text_encoder_use_attention_mask
```

The bundled planner reports whether instance/output directories and common model-cache hints are present; it does not run this training command.

### 3. Feed LoRA weights back into generation

After LoRA training, pass the output directory into a stage command, usually the coarse NeRF stage:

```bash
python launch.py --config configs/dreamcraft3d-coarse-nerf.yaml --train --gpu 0 \
  system.prompt_processor.prompt="$prompt" \
  data.image_path="$image_path" \
  system.guidance.lora_weights_path=".cache/if_dreambooth_mushroom"
```

The texture-stage config itself uses `stable-diffusion-bsd-guidance`; custom LoRA planning should remain consistent with the selected guidance implementation and the actual config keys available in the checkout.

## Decision checklist

- Are the core image sidecars valid? If not, route to image preparation first.
- Is the Janus/multiview issue visible enough to justify the optional branch?
- Are the Zero123++ and upscaler models cached locally if network is unavailable?
- Does the host expose the device assumed by the script (`cuda:1` in the source helper)?
- Is the `INSTANCE_DIR` populated with reasonable multiview images?
- Does the user accept long GPU training and checkpoint storage?

## What not to do

- Do not run downloads, model generation, or DreamBooth training as a quick diagnostic.
- Do not treat LoRA output as valid until it exists and contains expected training artifacts.
- Do not reuse stale `.cache/temp` images from a different prompt/object without checking them.
