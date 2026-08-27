# Troubleshooting

Use this guide to diagnose adapter/load failures before changing dependencies, model code, or weights.

## Optional Dependency Failures

Symptoms:

- `PEFT backend is required for this method.`
- `PEFT backend is required for set_adapters().`
- `low_cpu_mem_usage=True is not compatible with this peft version.`
- FaceID/IP-Adapter variants mention extra LoRA weights or PEFT.
- `transformers`, `safetensors`, `accelerate`, `opencv-python`, or `insightface` import errors appear in workflow-specific code.

Checks:

```bash
python scripts/adapter_state_check.py --class StableDiffusionPipeline --require-import peft --require-import safetensors
```

Resolution:

- If only diagnosing, report the missing optional dependency and the exact feature that needs it.
- Do not install broad extras unless the user approved environment mutation.
- If approved, install or upgrade the narrow dependency (`peft`, `safetensors`, `transformers`, `opencv-python`, etc.) instead of `diffusers[all]` by default.
- For `low_cpu_mem_usage=True` failures, either upgrade PEFT or set `low_cpu_mem_usage=False` for the adapter load.

## Device And Dtype Mistakes

Symptoms:

- CUDA dtype errors, CPU float16/bfloat16 failures, or mixed-device tensor errors.
- Image encoder, ControlNet, T2I-Adapter, UNet, transformer, or text encoder lands on a different device than the pipeline.
- IP-Adapter video workflow fails after CPU offload.

Resolution:

- Use `torch.float16` on CUDA for SD/SDXL when supported; use `torch.bfloat16` where the model family recommends it, such as many Flux paths.
- On CPU, prefer `torch.float32` unless the installed backend explicitly supports the lower dtype.
- Move loaded components consistently: pass `torch_dtype` during `from_pretrained`/`from_single_file`, then call `.to(device)` on the pipeline or component as needed.
- For IP-Adapter video/offload workflows, call `load_ip_adapter()` before `enable_model_cpu_offload()`.
- Do not pass strings such as `'float16'` where APIs expect an actual `torch.dtype`.

## Local Or Offline File Problems

Symptoms:

- `local_files_only=True` cannot find configs or weights.
- A directory contains multiple candidate weight files and Diffusers chooses the wrong one or cannot choose.
- Hub lookup errors occur in an offline task.
- A `.ckpt` file raises safety concerns.

Checks:

```bash
python scripts/adapter_state_check.py --path ./adapter.safetensors --expect-kind lora
python scripts/adapter_state_check.py --path ./model.safetensors --expect-kind single-file --config ./config
```

Resolution:

- Pass exact `weight_name`, `subfolder`, `config`, and `local_files_only=True`.
- For `from_single_file`, prefer a local Diffusers config directory supplied via `config`.
- If no local config exists, explain that one online cache-populating run or a downloaded config snapshot is required for reliable offline loading.
- Prefer `.safetensors` over `.ckpt` for untrusted checkpoints; `.ckpt` uses pickle and can be unsafe.
- Confirm the path is an adapter/checkpoint file, not an optimizer, scheduler, trainer state, or full training checkpoint directory.

## Adapter Name Collisions Or Activation Errors

Symptoms:

- `Adapter name <name> already in use in the model - please select a new adapter name.`
- `Adapter with name <name> already exists. Please use a different name.`
- `set_adapters('missing')` fails after loading with a different name.
- Multiple-adapter activation fails because one component lacks the requested adapter.

Resolution:

- Inspect `pipe.get_list_adapters()` and `pipe.get_active_adapters()`.
- Use stable unique names like `subject`, `style`, `detail`, or task-specific labels.
- If replacing intentionally in a hotswap path, call `enable_lora_hotswap` before the first adapter load and reload with `hotswap=True` using an existing adapter name.
- If replacing non-hotswap state, call `delete_adapters(name)` or `unload_lora_weights()` before reusing the name.
- For mixed state dicts, verify component prefixes (`unet`, `transformer`, `text_encoder`, `text_encoder_2`) match the selected pipeline family.

## Fuse, Unfuse, And Unload Order

Symptoms:

- Changing adapter weights has no effect after fusing.
- Removing LoRA after fused inference leaves unexpected output.
- Repeated fusing/unfusing creates confusing state.

Resolution:

1. Load adapters with explicit names.
2. Activate and weight them with `set_adapters`.
3. Run unfused inference while tuning.
4. Fuse only for final inference optimization.
5. Call `unfuse_lora()` before changing adapters or unloading.
6. Call `unload_lora_weights()` after unfusing to clear pipeline LoRA state.

Notes:

- `safe_fusing=True` checks for NaN values before merging.
- `adapter_names=[...]` on `fuse_lora` may require a recent PEFT version.
- For model components, PEFT uses `unload_lora()`; for pipelines, use `unload_lora_weights()`.

## LoRA Shape Or Key Mismatch

Symptoms:

- `Invalid LoRA checkpoint. Make sure all LoRA param names contain 'lora' substring.`
- Missing/unexpected key warnings after adapter load.
- Shape mismatch in `lora_A`, `lora_B`, text encoder, UNet, or transformer layers.
- Conversion warnings about unsupported DoRA scale, norm diff keys, `diff_b`, T5-XXL keys, or unsupported family-specific LoRA layout.

Resolution:

- Distinguish missing PEFT from actual weight mismatch: if PEFT is missing, dependency errors appear before or alongside adapter state work; if shapes/keys mismatch, the weight family or component prefixes are usually wrong.
- Confirm the LoRA was trained for the same model family and component layout as the target pipeline.
- Use family-specific pipeline loaders when available: SD/SDXL/SD3/Flux/Wan/Qwen/Z-Image and related families have dedicated conversion logic.
- Pass exact `weight_name` and `subfolder` to avoid loading the wrong file from a multi-file location.
- For PEFT component loading, set `prefix='unet'` or `prefix='transformer'` to isolate the target component from a mixed state dict.
- Do not silently drop incompatible tensors unless the loader documents a supported conversion path. Report the incompatibility and request matching weights.

## IP-Adapter Errors

Symptoms:

- `Required keys are (image_proj and ip_adapter) missing from the state dict.`
- `weight_name` and path list lengths differ.
- `weight_name` and `subfolder` list lengths differ.
- `Cannot assign N scale_configs to M IP-Adapter.`
- `Cannot assign N scales to M IP-Adapters.`
- Image encoder or feature extractor is missing for a variant that needs image inputs.

Resolution:

- Confirm IP-Adapter weights are not LoRA weights; regular state dicts need `image_proj` and `ip_adapter` sections.
- When loading multiple adapters, pass lists of equal length for path, `subfolder`, and `weight_name`.
- Use one float scale for one adapter or a list matching the loaded adapters.
- Use `image_encoder_folder=None` only with precomputed `ip_adapter_image_embeds` or variants that do not require loading an image encoder.
- For Plus variants, supply the compatible vision encoder before loading weights.
- For FaceID variants with extra LoRA weights, check PEFT availability.

## Textual Inversion Token Problems

Symptoms:

- Token already exists in tokenizer vocabulary.
- List of embeddings and list of `token` values have different lengths.
- Raw tensor embedding fails without a token.
- Prompt does not trigger the learned concept.

Resolution:

- Provide a unique `token` for raw tensor embeddings or when overriding loaded token names.
- Use equal-length lists for multiple embeddings and tokens.
- Include the token in `prompt` or `negative_prompt`; loading alone does not affect generation.
- For multi-vector embeddings, call or rely on `maybe_convert_prompt` so `<token>` expands to `<token> <token>_1 ...`.

## T2I-Adapter And ControlNet Workflow Errors

Symptoms:

- Control image count does not match `MultiAdapter` or multi-ControlNet count.
- `adapter_conditioning_scale` or `controlnet_conditioning_scale` length does not match controls.
- Control image dimensions or channel order are wrong.
- A SDXL ControlNet is used with SD/Flux/SD3 base, or vice versa.

Resolution:

- Match adapter/control checkpoints to the base model family and pipeline class.
- For `MultiAdapter`, keep `adapters`, `image=[...]`, and `adapter_conditioning_scale=[...]` in the same order and length.
- For ControlNet, use the family-specific ControlNet class and pipeline; do not load ControlNet weights through LoRA/IP-Adapter APIs.
- Convert control images to the expected PIL/RGB or tensor shape before pipeline call. Canny maps are commonly expanded to three channels.
- If a pipeline uses `control_image` rather than `image`, preserve the pipeline-specific argument name.

## Single-File Conversion Limitations

Symptoms:

- Local offline loading cannot find configs.
- `from_single_file` asks for only one of `config` and `original_config`.
- Component weights are missing in the checkpoint.
- GGUF pipeline loading fails.
- Pickle/ckpt safety warnings or concerns.

Resolution:

- Prefer `.safetensors` when available.
- Provide `config=<repo id or local config directory>` for reliable Diffusers component configs, especially with `local_files_only=True`.
- Use `original_config` only for legacy original-layout conversion when a Diffusers config path is unavailable.
- Do not pass both `config` and `original_config` to model-level single-file loaders.
- For GGUF, load supported model classes with `from_single_file(..., quantization_config=...)`, then pass the model into `PipelineClass.from_pretrained`; do not promise pipeline-level GGUF single-file loading.
- If the checkpoint omits a required component, ask for a matching checkpoint or pass the missing component explicitly as a pipeline argument.

## No Dedicated CLI Loader

Symptoms:

- User asks for `diffusers-cli lora`, `diffusers-cli load-adapter`, or similar.

Resolution:

- Explain that adapter loading is done through Python APIs in this Diffusers version.
- Provide a short Python loader script or use `scripts/single_file_loader_template.py` for a single-file skeleton.
- Use `diffusers-cli env` for environment reporting only, not adapter loading.
