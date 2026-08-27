# Conversion And Merge Workflows

Use these workflows to plan sd-scripts utility operations safely. Most listed utilities read and write large model files, so treat command lines as templates that must be adapted to the user's explicit paths, model family, and output policy.

## Universal Preflight

Before any merge, conversion, extraction, or resize:

1. Confirm model family: SD1, SD2, SDXL, SD3, FLUX, Hunyuan Image, Anima, Diffusers, or generic safetensors checkpoint.
2. Confirm source format: `.safetensors`, `.ckpt`, Diffusers directory, LoRA adapter, model component, or image file.
3. Inspect metadata if the file is `.safetensors`:

```bash
python skills/sd-scripts/sub-skills/model-utilities/scripts/inspect_safetensors_metadata.py INPUT.safetensors --include-keys --max-keys 30
```

4. Choose a new output path. Do not overwrite source files.
5. Estimate output size and ensure free disk space is comfortably larger than the largest input plus expected output.
6. Decide calculation and save precision. Prefer `float` for merge math when quality matters; save as `fp16` or `bf16` only when intended.
7. Decide device. CPU is safest but slower; GPU may be required or faster but can run out of memory.
8. Record rollback plan: original files remain unchanged, output path is disposable until validated.

## Read-Only Metadata Inspection

Use the bundled helper when the user asks what a `.safetensors` file contains or when planning a family-specific conversion.

```bash
python skills/sd-scripts/sub-skills/model-utilities/scripts/inspect_safetensors_metadata.py model.safetensors --include-keys --max-keys 20
```

Expected result:

- JSON object with `metadata`, `metadata_key_count`, and optionally `tensor_key_count` plus a bounded key sample.
- Non-zero exit for missing file, non-safetensors extension, unreadable header, or `--require-metadata` with no metadata.

Use metadata to look for `ss_*` LoRA keys, `modelspec.*` fields, architecture hints, merged-from history, rank/alpha hints, and trigger/usage hints. Metadata absence is common and should not by itself prove a file is invalid.

## LoRA Merge Planning

Pick the script by target family:

- SD1/SD2: `networks/merge_lora.py`
- SDXL: `networks/sdxl_merge_lora.py`
- FLUX: `networks/flux_merge_lora.py`

Planning checklist:

- Confirm all LoRAs target the same base family and compatible architecture.
- Count `--models` and `--ratios`; they must match.
- Decide whether the output is a merged LoRA or a full checkpoint with LoRAs applied.
- Use `--concat` only when intentionally increasing rank by concatenating dimensions instead of arithmetic merge.
- Keep `--no_metadata` off unless the user has a reason to suppress metadata.
- For SD2, SDXL, and FLUX, include the family-specific flags/paths instead of assuming SD1 defaults.

Template for a merged SD LoRA:

```bash
python networks/merge_lora.py --models A.safetensors B.safetensors --ratios 0.7 0.3 --save_to merged_lora.safetensors --precision float --save_precision fp16
```

Template for applying LoRAs into an SD checkpoint:

```bash
python networks/merge_lora.py --sd_model base.safetensors --models A.safetensors B.safetensors --ratios 0.7 0.3 --save_to merged_checkpoint.safetensors --precision float --save_precision fp16
```

Do not present these templates as final commands until paths, family flags, ratios, and output safety are confirmed.

## LoRA Extraction And Resize Planning

Extraction computes an approximate LoRA from differences between an original and tuned model. It can load two full checkpoints and run SVD.

Planning checklist:

- Match original and tuned models by architecture and version; do not compare SD1 to SD2, SDXL to SD1, or FLUX to SDXL.
- Choose rank/dim and convolution rank intentionally; too low loses detail, too high increases size.
- Select load/save precision separately when available.
- Plan memory: extraction may need CPU RAM and GPU VRAM depending on device flags.
- Validate output metadata and tensor shapes after extraction.

Resize is for rank reduction or dynamic rank selection. Use it on a copy of a LoRA, then validate output with metadata inspection and LoRA weight checks. Dynamic methods such as singular-value ratio/cumulative/Frobenius retention change rank based on tensor spectra; explain the trade-off to the user.

## Checkpoint Merge Planning

`tools/merge_models.py` averages multiple safetensors checkpoints.

Planning checklist:

- Inputs must be `.safetensors` files and must exist.
- Ratios default to equal weights; if provided, ratio count must match model count.
- Use `--unet_only` when only U-Net weights should be blended and first-model VAE/text encoder values should be preserved.
- `--show_skipped` helps diagnose keys present in later models but absent from the first model.
- Choose `--precision` for calculation and `--saving_precision` for final tensors.

Template:

```bash
python tools/merge_models.py --models baseA.safetensors baseB.safetensors --ratios 0.5 0.5 --output merged.safetensors --device cpu --precision float --saving_precision fp16 --show_skipped
```

## Diffusers And Original Checkpoint Conversion

`tools/convert_diffusers20_original_sd.py` converts SD v1/v2 Diffusers directories and original checkpoints.

Planning checklist:

- When loading a checkpoint, specify exactly one of `--v1` or `--v2`.
- Output is interpreted by path shape: extension means checkpoint, no extension means Diffusers directory.
- For Diffusers output, plan a reference model for scheduler/tokenizer config if defaults are not acceptable.
- `--fp16` affects Diffusers load and checkpoint save; `--save_precision_as` can set checkpoint save precision.
- `--metadata` is evaluated as a Python dictionary by the source script; only use trusted, carefully quoted metadata strings.

Template for Diffusers to checkpoint:

```bash
python tools/convert_diffusers20_original_sd.py --v1 --save_precision_as fp16 path/to/diffusers_dir output_model.safetensors
```

Template for checkpoint to Diffusers:

```bash
python tools/convert_diffusers20_original_sd.py --v1 --reference_model reference_diffusers_dir input_model.safetensors output_diffusers_dir
```

## FLUX, SD3, Hunyuan, And Anima Conversions

Use family-specific scripts rather than generic SD tools:

- `tools/convert_diffusers_to_flux.py`: FLUX Diffusers transformer shards to FLUX safetensors.
- `tools/merge_sd3_safetensors.py`: SD3/SD3.5 DiT, VAE, CLIP-L, CLIP-G, and T5-XXL component assembly.
- `networks/convert_flux_lora.py`: ai-toolkit ↔ sd-scripts FLUX LoRA key conversion.
- `networks/convert_anima_lora_to_comfy.py`: Anima LoRA conversion to/from ComfyUI.
- `networks/convert_hunyuan_image_lora_to_comfy.py`: Hunyuan Image LoRA conversion to/from ComfyUI.

Planning checklist:

- Verify source and destination conventions before command construction.
- For FLUX Diffusers, ensure all expected shards are present or the selected safetensors shard path pattern is valid.
- For SD3, confirm each optional component path is truly compatible with the DiT model.
- For conversion-to-Comfy workflows, preserve the source adapter and write to a new destination file.

## Image And Control Utility Planning

- Canny edge maps are small image transforms; confirm input/output paths and threshold values.
- Face rotate/crop writes many images. Use a separate destination directory, decide crop size/ratio, and account for `anime_face_detector` dependency.
- Latent upscaling requires VAE path, upscaler weights, image glob, output directory, batch sizes, and memory planning.
- Original ControlNet helper code is mostly for integration. When planning use, define preprocessing (`none` or `canny_th1_th2`), model path, weight, ratio, and hint images.
