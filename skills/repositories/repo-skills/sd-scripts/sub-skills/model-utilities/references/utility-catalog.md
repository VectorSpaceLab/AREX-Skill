# Utility Catalog

This catalog maps sd-scripts model/network utilities to safe use cases. It is distilled from the repository scripts and is self-contained for future agents; do not depend on source-repo docs at runtime.

## Network And LoRA Utilities

| Utility family | Use when | Key planning inputs | Safety notes |
| --- | --- | --- | --- |
| SD1/SD2 LoRA merge | Combining LoRA adapters or applying LoRA adapters into an SD checkpoint | `--models`, `--ratios`, optional `--sd_model`, `--v2`, `--precision`, `--save_precision`, `--save_to` | `--models` and `--ratios` must have equal length. With `--sd_model`, the base checkpoint is loaded and a new checkpoint is written. Without `--sd_model`, a merged LoRA is written. |
| SDXL LoRA merge | Combining or applying SDXL LoRAs | SDXL base/checkpoint inputs, ratios, optional layer block weights, precision, output path | Keep SDXL separate from SD1/SD2. Layer block weights add another dimension of ratio planning. |
| FLUX LoRA merge | Merging FLUX LoRAs or applying them to FLUX components | FLUX model paths, LoRA paths, ratios, precision, output path | FLUX uses different module/key layouts from SD/SDXL. Do not reuse SD LoRA merge scripts. |
| LoRA extraction | Extracting an approximate LoRA from original/tuned model differences | original model, tuned model, output path, rank/dim, convolution rank, precision, device, clamp/min-diff | SVD is memory-heavy and may load two full models. Match SD1/SD2/SDXL flags carefully. |
| FLUX LoRA extraction | Extracting a FLUX LoRA from model differences | original/tuned FLUX paths, output LoRA, rank, precision, device | FLUX-specific; do not use SD/SDXL extraction assumptions. |
| LoRA resize | Reducing rank or dynamically resizing LoRA tensors | source LoRA, output LoRA, target rank/convolution rank, dynamic method/threshold, device | Intended mainly for lower-rank approximation. Validate retained-rank metrics before replacing a production adapter. |
| LoRA weight check | Inspecting LoRA tensor names, shapes, and magnitude statistics | input LoRA file, optional all-key listing | Reads weights, not just metadata. Use for local files when tensor summary is needed. |
| FLUX LoRA conversion | Converting between ai-toolkit and sd-scripts FLUX LoRA key conventions | `--src`, `--dst`, `--src_path`, `--dst_path` | Source and destination formats must be explicit. Confirm no leftover/unconverted keys. |
| Anima/Hunyuan conversion | Converting sd-scripts and ComfyUI LoRA formats for these families | source path, destination path, optional reverse flag | Family-specific mappings; do not generalize to SDXL or FLUX. |

## Checkpoint And Diffusers Utilities

| Utility | Use when | Key planning inputs | Safety notes |
| --- | --- | --- | --- |
| Diffusers/original SD conversion | Convert SD v1/v2 between Diffusers directory and checkpoint file | `--v1` or `--v2` for checkpoint load, input path, output path, precision flags, optional reference model | Output type is inferred from whether the save path has an extension. Diffusers load can use `--variant`; checkpoint save precision can be fp16/bf16/float. |
| FLUX Diffusers conversion | Convert a FLUX Diffusers transformer shard set or first shard into a single FLUX safetensors file | `--diffusers_path`, `--save_to`, optional `--mem_eff_load_save`, optional `--save_precision` | Expects three transformer shards when given a shard path pattern. Uses FLUX key maps; missing keys abort conversion. |
| Safetensors checkpoint averaging | Merge multiple safetensors checkpoints by weighted average | `--models`, optional `--ratios`, `--output`, `--unet_only`, `--precision`, `--saving_precision`, `--device` | Only accepts `.safetensors`. Defaults to equal ratios. Missing keys are skipped or filled from first model depending on key class. |
| SD3 component merge | Assemble SD3/SD3.5 components into one safetensors file | DiT path plus optional VAE, CLIP-L, CLIP-G, T5-XXL, output path, device, save precision | Adds expected prefixes for components and writes one large file. Confirm component compatibility and available disk. |

## Metadata And Model Spec Helpers

- Safetensors metadata can be read without loading tensors. Prefer `scripts/inspect_safetensors_metadata.py` for safe inspection.
- sd-scripts writes or reads LoRA metadata keys such as `ss_v2`, `ss_base_model_version`, `ss_network_module`, `ss_network_dim`, `ss_network_alpha`, and `ss_network_args`.
- SAI ModelSpec metadata uses `modelspec.*` keys including architecture, implementation, title, resolution, hash, merged-from, prediction type, and adapter family.
- Hash helpers distinguish legacy WebUI-style partial hashes from safetensors payload hashes; avoid recalculating or rewriting hashes unless a utility is explicitly saving a new file.

## ControlNet And Image Helpers

| Utility | Use when | Notes |
| --- | --- | --- |
| `tools/canny.py` equivalent workflow | Produce a Canny edge map from an image | Requires OpenCV. Inputs and outputs are normal image files; choose thresholds intentionally. |
| Face rotate/crop helper | Detect anime faces, optionally rotate, crop, resize, and write derived images | Requires `anime_face_detector`, OpenCV, NumPy. It writes output images; use a separate destination directory. |
| Latent upscaler helper | Upscale images through a VAE-backed latent upscaler | Requires Diffusers, Torch, VAE path, weights path, and enough device memory. |
| Original ControlNet helper | Load original ControlNet weights and preprocess hints for integration with the original U-Net path | Mainly a library/helper workflow, not a standalone user-facing conversion command. Supports canny preprocessing strings. |

## Routing Boundaries

- Training setup, optimizer/network module selection, and save/resume policies belong to `../training`.
- Sampling, prompt generation, and inference command construction belong to `../generation`.
- Dataset validation, caption generation, bucket/cache creation, and image dataset hygiene belong to `../data-preparation` unless the requested action is one of the utility image transforms above.
