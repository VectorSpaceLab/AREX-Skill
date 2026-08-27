---
name: adapters-and-loaders
description: "Use when a Diffusers task involves loading, composing, validating,
  fusing, unloading, or diagnosing LoRA/PEFT adapters, textual inversion
  embeddings, IP-Adapters, T2I-Adapters, ControlNet components, or single-file
  checkpoints."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Adapters And Loaders

Use this sub-skill for adapter and checkpoint-loading work after the base Diffusers environment and pipeline family are known.

## Route Here For

- LoRA pipeline loading with `load_lora_weights`, `adapter_name`, `set_adapters`, `fuse_lora`, `unfuse_lora`, `unload_lora_weights`, `delete_adapters`, `get_list_adapters`, and `enable_lora_hotswap`.
- PEFT component adapters on UNet/transformer classes with `load_lora_adapter`, `add_adapter`, `set_adapter`, `set_adapters`, `enable_lora`, `disable_lora`, `fuse_lora`, `unfuse_lora`, `unload_lora`, and `delete_adapters`.
- Textual inversion with `load_textual_inversion`, `token`, `weight_name`, negative embeddings, and multi-vector prompt conversion.
- IP-Adapter loading with `load_ip_adapter`, `set_ip_adapter_scale`, `unload_ip_adapter`, image encoder choices, FaceID/Plus variants, and `ip_adapter_image_embeds`.
- T2I-Adapter and ControlNet component loading plans, including `T2IAdapter.from_pretrained`, `MultiAdapter`, `ControlNetModel.from_pretrained`, and passing components into compatible pipelines.
- Single-file checkpoint loading with `from_single_file`, local `config`, `original_config`, safetensors/ckpt/DDUF/GGUF decisions, and offline path checks.

## Route Elsewhere

- End-to-end generation, prompt tuning, scheduler choice during inference, memory/offload execution, or image postprocessing: use `../pipelines-and-inference/SKILL.md`.
- Training LoRA/textual inversion/adapter weights: use `../training-recipes/SKILL.md`.
- Conversion scripts, repository maintenance, copied-code propagation, or docs build work: use `../conversion-and-maintenance/SKILL.md`.

## Fast Workflow

1. Classify the request: LoRA/PEFT, textual inversion, IP-Adapter, T2I-Adapter, ControlNet component, or single-file checkpoint.
2. Run a no-download preflight for local files and imports when useful: `python scripts/adapter_state_check.py --path ./weights.safetensors --class StableDiffusionXLPipeline`.
3. Choose explicit names and paths before loading: `adapter_name`, `weight_name`, `subfolder`, `token`, `config`, `local_files_only`, device, and dtype.
4. Use `references/workflows.md` for copy-ready loading plans and `references/api-map.md` for the method surface.
5. If an error mentions PEFT, adapter names, missing keys, shape mismatch, offline configs, image encoders, scale length, or device/dtype, use `references/troubleshooting.md` before changing dependencies or model code.

## Key Rules

- Use explicit `adapter_name` values for every LoRA/PEFT load; inspect `get_list_adapters()` and `get_active_adapters()` before activating, fusing, or deleting adapters.
- Treat `fuse_lora` as a final inference optimization. Call `unfuse_lora()` before changing adapter combinations and keep unfused state if reversibility matters.
- For local/offline work, pass exact `weight_name`, `subfolder`, `config`, and `local_files_only=True`; do not rely on Hub sibling lookup or config inference.
- Match components to pipeline family: SD/SDXL usually use `unet`; SD3/Flux/newer transformer pipelines usually use `transformer`; SDXL can include `text_encoder_2`.
- ControlNet and T2I-Adapter are loaded as separate components and passed into compatible pipelines; they are not LoRA weights.
- Prefer `.safetensors` over `.ckpt` for untrusted files; `.ckpt` can execute pickle payloads during loading.

## References

- Adapter workflows: `references/workflows.md`
- API map: `references/api-map.md`
- Troubleshooting: `references/troubleshooting.md`
- Safe checker: `scripts/adapter_state_check.py`
- Single-file template: `scripts/single_file_loader_template.py`
