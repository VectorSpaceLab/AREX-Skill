# Conversion Workflows

This reference gives self-contained plans for Diffusers conversion work. The bundled `scripts/conversion_command_builder.py` prints safe argument plans for common families and never runs conversion, downloads weights, or pushes to the Hub. It emits a `<user-conversion-entrypoint.py>` placeholder that must be replaced with a user-owned or explicitly provided conversion entrypoint.

## First Questions

- What is the source format: original Stable Diffusion checkpoint, Diffusers directory, LoRA safetensors, fully fine-tuned model pair, or Diffusers directory to ONNX?
- Is the input local-only or allowed to download configs/models from the Hub?
- Is the output a Diffusers directory, a single-file `.safetensors`/`.ckpt`, a LoRA `.safetensors`, or an ONNX directory?
- What device and dtype are safe: CPU/float32 for broad compatibility, CUDA/float16 for memory-heavy conversion/export, or explicit CPU conversion with no `--half`?
- Should the result remain local, or is a Hub PR/push explicitly requested?

## Original Stable Diffusion Checkpoint To Diffusers

Use the original Stable Diffusion conversion family when the input is a `.ckpt` or `.safetensors` checkpoint from the original ecosystem and the output should be a Diffusers model directory.

Skeleton:

```bash
python <user-conversion-entrypoint.py> \
  --checkpoint_path ./model.safetensors \
  --dump_path ./converted-diffusers \
  --from_safetensors \
  --to_safetensors \
  --device cpu
```

Important options:

- `--checkpoint_path` is required and points to the source checkpoint.
- `--dump_path` is required and points to a local output directory.
- `--original_config_file` or `--config_files` may be needed when model architecture cannot be inferred.
- `--scheduler_type` accepts families such as `pndm`, `lms`, `ddim`, `euler`, `euler-ancestral`, and `dpm`.
- `--image_size` and `--prediction_type` disambiguate SD v1, SD v2 base, and SD v2 768-style checkpoints.
- `--from_safetensors` is required when reading safetensors through the script; `--to_safetensors` writes safer output weights.
- `--half` saves half precision weights; combine with a compatible device and only when reduced precision is intended.
- `--controlnet` saves only the converted ControlNet model instead of a full pipeline.
- `--pipeline_class_name` selects a concrete Diffusers pipeline class when automatic inference is not enough.

Safety plan for a local checkpoint with no accidental Hub push:

1. Confirm the checkpoint path is local and readable; prefer `.safetensors`.
2. Choose a local `--dump_path` that does not already contain important files.
3. Build the command skeleton with `conversion_command_builder.py --family original-sd-to-diffusers`.
4. Keep the conversion script local: it calls `save_pretrained` and does not push by default.
5. After conversion, validate with a local load or inspection task using the inference sub-skill, not by immediately uploading.

## Diffusers Directory To Original SD Or SDXL Single File

Use these families when the input is already in Diffusers format and the output should be a community-compatible checkpoint.

Stable Diffusion skeleton:

```bash
python convert_diffusers_to_original_stable_diffusion.py \
  --model_path ./diffusers-model \
  --checkpoint_path ./model.safetensors \
  --use_safetensors
```

SDXL skeleton:

```bash
python convert_diffusers_to_original_sdxl.py \
  --model_path ./sdxl-diffusers-model \
  --checkpoint_path ./sdxl-model.safetensors \
  --use_safetensors
```

Important options:

- `--model_path` must be a Diffusers directory containing component subfolders such as `unet`, `vae`, and text encoder folders.
- `--checkpoint_path` is the target single-file output.
- `--use_safetensors` writes safetensors; otherwise the script writes a `.ckpt`-style file.
- `--half` stores half precision weights and should be intentional.

## LoRA Safetensors Merge To Diffusers Pipeline

Use the LoRA safetensors merge family when the user wants to merge a LoRA safetensors checkpoint into a base Stable Diffusion pipeline and save a new Diffusers directory.

Skeleton:

```bash
python <user-conversion-entrypoint.py> \
  --base_model_path ./base-diffusers-model \
  --checkpoint_path ./adapter.safetensors \
  --dump_path ./merged-pipeline \
  --to_safetensors \
  --alpha 0.75 \
  --device cpu
```

Important options:

- `--base_model_path`, `--checkpoint_path`, and `--dump_path` are required.
- `--lora_prefix_unet` defaults to `lora_unet`; `--lora_prefix_text_encoder` defaults to `lora_te`.
- `--alpha` controls the merge ratio in `W = W0 + alpha * deltaW`.
- This script mutates the loaded base pipeline weights and saves a merged model; use adapter APIs instead when reversible composition is needed.

## Extract LoRA From A Fine-Tuned Model Pair

Use the LoRA extraction family when comparing a base model and a fully fine-tuned model to approximate the delta as LoRA weights.

Skeleton:

```bash
python <user-conversion-entrypoint.py> \
  --base_ckpt_path ./base-model \
  --base_subfolder transformer \
  --finetune_ckpt_path ./finetuned-model \
  --finetune_subfolder transformer \
  --rank 64 \
  --lora_out_path ./extracted-lora.safetensors
```

Notes:

- The script is model-class-specific in the evidence: it imports `CogVideoXTransformer3DModel` and may require code edits for other model families.
- `--lora_out_path` must end with `.safetensors`.
- CUDA is strongly preferred for speed during SVD-heavy extraction.
- Route training/fine-tuning decisions to `training-recipes`; route loading the extracted LoRA to `adapters-and-loaders`.

## Stable Diffusion Diffusers Directory To ONNX

The repository includes a reference Stable Diffusion ONNX script, but current docs emphasize Optimum for ONNX Runtime export and inference.

Script skeleton:

```bash
python <user-conversion-entrypoint.py> \
  --model_path ./sd-diffusers-model \
  --output_path ./sd-onnx \
  --opset 14
```

Important options:

- `--model_path` can be a local Diffusers directory or Hub model id.
- `--output_path` is required and receives component ONNX subfolders.
- `--opset` defaults to `14`.
- `--fp16` requires CUDA; the script raises `ValueError` when fp16 export is requested without CUDA.
- ONNX Runtime inference usually uses Optimum classes such as `ORTStableDiffusionPipeline` and `ORTStableDiffusionXLPipeline`; route actual inference to `pipelines-and-inference` after export.

## Single-File Loading Or Re-Saving Without Scripts

For some requests, a script is unnecessary. Diffusers can load a single file with `from_single_file` and save a Diffusers directory with `save_pretrained`.

```python
from diffusers import StableDiffusionXLPipeline

pipeline = StableDiffusionXLPipeline.from_single_file(
    "./model.safetensors",
    config="./local-config-directory",
    local_files_only=True,
)
pipeline.save_pretrained("./converted-diffusers", safe_serialization=True)
```

Rules:

- Pass `config` for local/offline files when automatic inference may need Hub metadata.
- Use `local_files_only=True` when downloads are not allowed.
- Use `safe_serialization=True` for Diffusers output when possible.
- Avoid `.ckpt` from untrusted sources; prefer `.safetensors`.
