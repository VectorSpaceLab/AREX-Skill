# Troubleshooting Model Utilities

Use this guide when sd-scripts model, LoRA, conversion, metadata, ControlNet, or image utilities fail or when planning risks need to be explained before execution.

## Format Mismatch

Symptoms:

- Script expects `.safetensors` but receives `.ckpt` or a directory.
- Diffusers conversion treats an output path unexpectedly as checkpoint or directory.
- LoRA converter reports missing keys or leaves unconverted tensors.

Actions:

- Confirm file extension and actual structure before running. A Diffusers model is a directory with component subfolders/configs; a checkpoint is a single file.
- For `tools/merge_models.py`, use only `.safetensors` checkpoints.
- For `tools/convert_diffusers20_original_sd.py`, remember: save path with an extension means checkpoint; save path without an extension means Diffusers directory.
- Use metadata/key inspection to identify `ss_*`, `modelspec.*`, FLUX transformer keys, SD checkpoint prefixes, or LoRA key styles.

## Missing `safetensors`

Symptoms:

- `ModuleNotFoundError: No module named 'safetensors'`.
- Bundled metadata helper exits with a safetensors-required message.

Actions:

- Install `safetensors` in the active environment before metadata inspection or safetensors utilities.
- If the task only needs planning, do not mutate the environment without user approval; explain the missing dependency and provide the intended command.

## Incompatible LoRA Architecture Or Model Family

Symptoms:

- Missing module names during merge.
- Shape mismatch assertions.
- Poor output quality after apparently successful merge.
- Conversion script cannot find expected keys.

Actions:

- Separate SD1/SD2, SDXL, SD3, FLUX, Hunyuan Image, and Anima workflows.
- Match LoRA adapters to the intended base model family and implementation.
- For SD2, include version/prediction flags where required.
- For FLUX and newer families, use the dedicated conversion/merge scripts rather than SD/SDXL scripts.
- Inspect `ss_base_model_version`, `ss_network_module`, `ss_network_dim`, `ss_network_alpha`, and `modelspec.architecture` when present.

## Ratio Count Or Weight Planning Errors

Symptoms:

- Assertion that model count and ratio count differ.
- Unexpected equal averaging because ratios were omitted.
- Output dominated by the wrong input.

Actions:

- Count all input models/adapters and all ratio values before constructing the command.
- Make ratios explicit for reproducibility, even when equal weights are intended.
- For LoRA merge, `--models A B C --ratios 0.5 0.3 0.2` is valid; `--models A B C --ratios 0.5 0.5` is invalid.
- For checkpoint averaging, document whether ratios are intended to sum to 1.0; scripts may not normalize user intent for every workflow.

## Accidental Overwrite And Output Path Safety

Symptoms:

- User proposes saving to an input path.
- Output file already exists.
- Conversion writes a directory when a single file was intended, or vice versa.

Actions:

- Refuse to run destructive commands until a distinct output path is chosen.
- Prefer a fresh output directory for each merge/conversion attempt.
- Include operation, family, and precision in output names, such as `portrait_sdxl_lora_mix_fp16.safetensors`.
- For Diffusers conversion, verify whether the output path has an extension and explain the consequence.

## Low Disk Space

Symptoms:

- Save fails partway through.
- System becomes slow or full during large checkpoint conversion.
- Temporary or final files are truncated.

Actions:

- Estimate at least input size plus output size plus working headroom before conversion.
- For SD3/FLUX component merges, account for multiple components plus a large final file.
- Prefer memory-efficient options where supported, such as FLUX conversion `--mem_eff_load_save` or SD3 merge internals that use memory-efficient safetensors save.
- Validate output size and metadata after completion before deleting any input.

## Missing Keys Or Metadata

Symptoms:

- Metadata inspection shows empty metadata.
- Merge warns that keys are not in all models.
- FLUX conversion reports a key not found in the map.

Actions:

- Empty metadata is common; inspect key samples before declaring a file unusable.
- For checkpoint merge missing keys, decide whether first-model fallback behavior is acceptable or whether the model set is incompatible.
- For FLUX/Hunyuan/Anima conversions, missing mapped keys usually means the source format or version is not what was selected.
- If metadata matters for publishing, plan a conversion or save path that writes SAI ModelSpec or `ss_*` metadata where the utility supports it.

## Device Memory Failures

Symptoms:

- CUDA out-of-memory during extraction, conversion, or latent upscaling.
- Process killed during SVD or model load.
- GPU memory remains high after failure.

Actions:

- Retry on CPU if time permits and the script supports it.
- Lower batch sizes for latent upscaling.
- Lower extraction rank or use lower load precision only if quality trade-offs are acceptable.
- Use memory-efficient load/save options where supported.
- Close other GPU workloads before retrying.

## SD3, FLUX, Hunyuan, And Anima Differences

Symptoms:

- A command that worked for SDXL fails for FLUX or Hunyuan.
- Key names include transformer block patterns instead of U-Net LoRA names.
- Converted LoRA does not load in ComfyUI or sd-scripts.

Actions:

- Use the family-specific utility and name the source/destination convention explicitly.
- FLUX LoRA conversion supports ai-toolkit and sd-scripts conventions; do not assume PEFT or ComfyUI mappings are equivalent unless the script says so.
- Hunyuan Image and Anima each have dedicated ComfyUI conversion scripts; use `--reverse` only after confirming direction.
- SD3 component merge requires compatible DiT, VAE, CLIP-L, CLIP-G, and T5-XXL component naming/prefixes.

## Image Helper Failures

Symptoms:

- Canny output is empty or all white/black.
- Face detector finds no faces.
- Latent upscaler fails to load VAE or weights.

Actions:

- For Canny, adjust thresholds and confirm image read succeeded.
- For face rotate/crop, confirm supported image extensions, face size thresholds, and `anime_face_detector` availability.
- Use a separate destination directory for face crops to avoid mixing derived files with originals.
- For latent upscaler, verify VAE path, upscaler weights, image glob expansion, batch size, and device memory.

## When To Stop And Ask

Ask the user before proceeding when:

- The output path could overwrite or replace a source model.
- The command will write multi-GB files and available disk is uncertain.
- The selected family is ambiguous from metadata and filenames.
- The task requires installing missing dependencies or using GPU resources.
- The conversion would evaluate user-supplied metadata strings or otherwise execute untrusted content.
