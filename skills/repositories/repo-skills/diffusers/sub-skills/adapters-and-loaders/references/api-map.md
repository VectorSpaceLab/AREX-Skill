# API Map

This map captures the Diffusers adapter and loader surface needed for coding tasks without reopening the source repository.

## Installed Package Facts

- Package line inspected for this skill: `diffusers 0.39.0.dev0`.
- Public objects confirmed in the inspection environment include `DiffusionPipeline`, `AutoPipelineForText2Image`, `StableDiffusionPipeline`, `ControlNetModel`, and `T2IAdapter`.
- `ControlNetModel.__init__` accepts structural parameters such as `in_channels=4`, `conditioning_channels=3`, `cross_attention_dim=1280`, `controlnet_conditioning_channel_order='rgb'`, and `global_pool_conditions=False`.
- `T2IAdapter.__init__` accepts `in_channels=3`, `channels=[320, 640, 1280, 1280]`, `num_res_blocks=2`, `downscale_factor=8`, and `adapter_type='full_adapter'`.
- Adapter loading is Python API work. The Diffusers CLI does not provide a dedicated LoRA/textual-inversion/IP-Adapter loader command.

## Loader Modules

- `diffusers.loaders.lora_base`: shared `LoraBaseMixin`, adapter state helpers, `LORA_WEIGHT_NAME`, and `LORA_WEIGHT_NAME_SAFE`.
- `diffusers.loaders.lora_pipeline`: pipeline LoRA mixins for Stable Diffusion, SDXL, SD3, Flux/Flux2, CogVideoX, Mochi, LTX/LTX2, Sana, Helios, HunyuanVideo, Wan, Qwen Image, Z-Image, Cosmos, Ideogram, Ernie Image, and related families.
- `diffusers.loaders.peft`: `PeftAdapterMixin` for model-component PEFT adapter operations.
- `diffusers.loaders.textual_inversion`: `TextualInversionLoaderMixin`.
- `diffusers.loaders.ip_adapter`: `IPAdapterMixin`, `ModularIPAdapterMixin`, `FluxIPAdapterMixin`, and `SD3IPAdapterMixin`.
- `diffusers.loaders.single_file`: pipeline-level `FromSingleFileMixin`.
- `diffusers.loaders.single_file_model`: model-level `FromOriginalModelMixin`.
- `diffusers.loaders.unet`, `transformer_sd3`, and `transformer_flux`: component loading mixins for UNet/transformer classes, including IP-Adapter attention processor paths in relevant families.

## LoRA Pipeline Methods

Common methods inherited by LoRA-capable pipelines:

- `load_lora_weights(pretrained_model_name_or_path_or_dict, adapter_name=None, hotswap=False, **kwargs)`: load LoRA from a Hub id, local directory/file, or state dict. Common kwargs include `weight_name`, `subfolder`, `cache_dir`, `local_files_only`, `revision`, `token`, `use_safetensors`, and `low_cpu_mem_usage`.
- `lora_state_dict(pretrained_model_name_or_path_or_dict, **kwargs)`: parse LoRA state and optional network alphas.
- `save_lora_weights(...)`: save component LoRA weights; supported component arguments vary by pipeline family.
- `set_adapters(adapter_names, adapter_weights=None)`: activate and weight one or more named adapters. Some families support nested component/block weights.
- `fuse_lora(components=..., lora_scale=1.0, safe_fusing=False, adapter_names=None)`: merge active or named LoRA layers into base weights.
- `unfuse_lora(components=..., **kwargs)`: undo a previous LoRA fuse.
- `unload_lora_weights(...)`: remove pipeline LoRA state. Flux-family paths may expose `reset_to_overwritten_params=False` for overwritten-parameter cases.
- `disable_lora()` and `enable_lora()`: toggle loaded LoRA layers without deleting them.
- `delete_adapters(adapter_names)`: delete named adapters.
- `get_active_adapters() -> list[str]`: report active adapter names.
- `get_list_adapters() -> dict[str, list[str]]`: report loaded adapter names by component.
- `enable_lora_hotswap(**kwargs)`: prepare for hotswapping adapters, usually with `target_rank=max_rank` before the first load.

Component naming guide:

- Stable Diffusion: `unet`, `text_encoder`.
- SDXL: `unet`, `text_encoder`, `text_encoder_2`.
- SD3 and many transformer pipelines: `transformer`, `text_encoder`, `text_encoder_2`.
- Flux: `transformer`, `text_encoder`; Flux LoRA may include transformer-specific conversion paths.
- Video and newer image pipelines often fuse/unfuse only `transformer`.

## PEFT Component Methods

Use these on components that include `PeftAdapterMixin`, such as many UNet and transformer classes.

- `load_lora_adapter(pretrained_model_name_or_path_or_dict, prefix='transformer', hotswap=False, **kwargs)`: load a component adapter from a mixed or component state dict.
- `add_adapter(adapter_config, adapter_name='default')`: inject a PEFT adapter config.
- `set_adapter(adapter_name)`: activate adapter(s) on one component.
- `set_adapters(adapter_names, weights=None)`: activate and weight multiple adapters on one component.
- `fuse_lora(lora_scale=1.0, safe_fusing=False, adapter_names=None)`: merge PEFT LoRA layers.
- `unfuse_lora()`: unmerge PEFT LoRA layers.
- `unload_lora()`: remove PEFT LoRA layers from a component.
- `disable_lora()` and `enable_lora()`: toggle component adapter layers.
- `delete_adapters(adapter_names)`: delete named component adapters.
- `enable_lora_hotswap(target_rank, check_compiled='error')`: prepare a model for compiled LoRA hotswapping.

PEFT-dependent methods raise errors such as `PEFT backend is required for this method` or `PEFT backend is required for set_adapters()` when `peft` is absent or too old.

## Textual Inversion Methods

- `load_textual_inversion(pretrained_model_name_or_path, token=None, tokenizer=None, text_encoder=None, **kwargs)`: load one or more embeddings into tokenizer/text encoder. Common kwargs include `weight_name`, `cache_dir`, `local_files_only`, `hf_token`, `revision`, `subfolder`, and `use_safetensors`.
- `maybe_convert_prompt(prompt, tokenizer)`: expand multi-vector textual inversion tokens in prompts.

Default file names are `learned_embeds.safetensors` and `learned_embeds.bin`. Supported state formats include Diffusers single-key dicts, Automatic1111 dictionaries with `string_to_param`, raw tensors when `token` is supplied, and lists of those formats.

## IP-Adapter Methods

- `load_ip_adapter(pretrained_model_name_or_path_or_dict, subfolder, weight_name, image_encoder_folder='image_encoder', **kwargs)`: load IP-Adapter state into the pipeline UNet/transformer. `pretrained_model_name_or_path_or_dict`, `subfolder`, and `weight_name` may be lists with matching lengths.
- `set_ip_adapter_scale(scale)`: set adapter influence. Stable Diffusion supports floats and granular dictionaries; Flux supports `float | list[float] | list[list[float]]`; SD3 supports a float.
- `unload_ip_adapter()`: remove IP-Adapter attention processors and related projection/encoder state.
- `is_ip_adapter_active`: available on SD3 IP-Adapter mixin; confirm on the selected class before relying on it.

State requirements:

- Regular IP-Adapter state dicts contain top-level `image_proj` and `ip_adapter` sections.
- Safetensors files are split by `image_proj.` and `ip_adapter.` prefixes during load.
- FaceID variants may include extra LoRA weights and can require PEFT support.

## T2I-Adapter And ControlNet Component APIs

- `T2IAdapter.from_pretrained(path_or_id, torch_dtype=...)`: load a T2I adapter conditioned on one control type such as canny or depth.
- `MultiAdapter([adapter_a, adapter_b, ...])`: compose multiple T2I adapters; pass a matching list of control images and `adapter_conditioning_scale` values at inference.
- `ControlNetModel.from_pretrained(path_or_id, torch_dtype=...)`: load SD/SDXL ControlNet components.
- Family-specific ControlNet classes include Flux, SD3, Hunyuan-DiT, and other pipeline-specific variants; choose the ControlNet class that matches the pipeline family.
- Pass ControlNet/T2I components into `PipelineClass.from_pretrained(..., controlnet=controlnet)` or `... adapter=adapter`; these are not loaded with `load_lora_weights`.

## Single-File Methods

- Pipeline method: `PipelineClass.from_single_file(pretrained_model_link_or_path, **kwargs)` from `FromSingleFileMixin`.
- Model method: `ModelClass.from_single_file(pretrained_model_link_or_path_or_dict=None, **kwargs)` from `FromOriginalModelMixin`.

Common kwargs:

- `config`: Diffusers model/pipeline config repo id or local config directory. Prefer this for offline reliability.
- `original_config`: legacy original YAML/config path or URL for LDM-style conversion paths.
- `torch_dtype`: actual `torch.dtype`; invalid non-dtype values default to `torch.float32` with a warning.
- `local_files_only`: prevent Hub access when all files/configs are local.
- `disable_mmap`: disable memory mapping for checkpoint loading.
- `device_map`: dispatch after conversion in supported cases.
- `quantization_config`: coordinate supported model-level quantization cases such as GGUF/Quanto.

Selection rules:

- Do not pass both `config` and `original_config` to model-level `from_single_file`; it raises `ValueError` asking for only one.
- For local checkpoints, prefer `config=<local Diffusers config directory>` over inference from checkpoint metadata.
- Pipeline-level GGUF loading is not the documented path; load supported GGUF model classes with `from_single_file` and assemble the pipeline with `from_pretrained`.
