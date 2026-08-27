# Adapter And Loader Workflows

Use these safe, repeatable plans for Diffusers adapter and checkpoint-loading tasks.

## Preflight Without Downloads

Run the bundled checker from this sub-skill directory or from an installed skill copy:

```bash
python scripts/adapter_state_check.py --class StableDiffusionPipeline --class StableDiffusionXLPipeline --class FluxPipeline
python scripts/adapter_state_check.py --path ./adapter.safetensors --expect-kind lora --require-import peft --require-import safetensors
```

Expected signal: JSON with dependency availability, class method signatures, and local path checks. The script never downloads weights and never instantiates large models.

## LoRA On Pipelines

Use pipeline LoRA methods when the user has a Diffusers pipeline and wants style, subject, or task adaptation weights.

```python
pipe = StableDiffusionXLPipeline.from_pretrained(model_id, torch_dtype=torch.float16).to("cuda")
pipe.load_lora_weights(lora_dir, weight_name="pytorch_lora_weights.safetensors", adapter_name="cinematic")
pipe.load_lora_weights(other_lora_dir, weight_name="pixel-art-xl.safetensors", adapter_name="pixel")
pipe.set_adapters(["cinematic", "pixel"], adapter_weights=[0.6, 0.4])
print(pipe.get_list_adapters())
print(pipe.get_active_adapters())
```

Rules:

- Always give every adapter a stable `adapter_name`.
- Use exact `weight_name` when a directory/repo contains multiple `.safetensors` or `.bin` files.
- For offline/local loading, add `local_files_only=True` and pass the exact local directory or file path.
- If the adapter was trained for a different family, do not force-load by dropping keys; report the mismatch.

## Fuse, Unfuse, And Unload

Fuse only after the final adapter combination is selected for inference.

```python
pipe.set_adapters(["cinematic", "pixel"], adapter_weights=[0.6, 0.4])
pipe.fuse_lora(lora_scale=1.0, safe_fusing=True, adapter_names=["cinematic", "pixel"])
# run inference
pipe.unfuse_lora()
pipe.unload_lora_weights()
```

Order rules:

1. Load adapters with explicit names.
2. Activate and weight adapters with `set_adapters`.
3. Run unfused inference while tuning weights.
4. Fuse for final inference optimization only.
5. Call `unfuse_lora()` before changing weights/names or unloading.
6. Call `unload_lora_weights()` to clear pipeline LoRA state.

For component-level PEFT state, use `unload_lora()` on the component instead of `unload_lora_weights()` on the pipeline.

## PEFT Model Components

Use PEFT model-level methods when operating on a component such as `pipe.unet`, `pipe.transformer`, or a Diffusers model class with `PeftAdapterMixin`.

```python
pipe.unet.load_lora_adapter(lora_dir_or_state_dict, prefix="unet", adapter_name="detail")
pipe.unet.set_adapters(["detail"], weights=[0.8])
pipe.unet.disable_lora()
pipe.unet.enable_lora()
pipe.unet.delete_adapters("detail")
```

Use `prefix` to select component keys from a mixed state dict. Common prefixes are `unet`, `transformer`, `text_encoder`, and `text_encoder_2`.

For compiled model hotswapping:

```python
pipe.enable_lora_hotswap(target_rank=max_rank)
pipe.load_lora_weights(first_lora, adapter_name="subject")
# compile if needed
pipe.load_lora_weights(replacement_lora, adapter_name="subject", hotswap=True)
```

Constraints:

- Call `enable_lora_hotswap` before loading the first adapter if rank growth is possible.
- `hotswap=True` expects the adapter name to already exist.
- Do not promise text encoder hotswapping unless the selected loader explicitly supports it.

## Textual Inversion

Use textual inversion for learned tokens/embeddings, not attention adapters.

```python
pipe.load_textual_inversion(
    text_inv_dir_or_file,
    weight_name="learned_embeds.safetensors",
    token="<my-style>",
)
image = pipe("portrait in <my-style> style").images[0]
```

For negative embeddings:

```python
pipe.load_textual_inversion(
    negative_embedding_dir_or_file,
    weight_name="easynegative.safetensors",
    token="easynegative",
)
image = pipe(prompt, negative_prompt="easynegative").images[0]
```

Signals:

- A duplicate token already in tokenizer vocabulary raises an error; choose a new token.
- Multi-vector embeddings expand prompt tokens via `maybe_convert_prompt`; ensure the loaded token appears in `prompt` or `negative_prompt`.
- Raw tensor embeddings require an explicit `token`.

## IP-Adapter

Use IP-Adapter when the user wants image-prompt conditioning in addition to text prompts.

```python
pipe.load_ip_adapter(
    ip_adapter_dir,
    subfolder="sdxl_models",
    weight_name="ip-adapter_sdxl.bin",
)
pipe.set_ip_adapter_scale(0.8)
image = pipe(prompt="a product photo", ip_adapter_image=reference_image).images[0]
```

Multiple IP-Adapters require aligned lists:

```python
pipe.load_ip_adapter(
    [repo_or_dir_a, repo_or_dir_b],
    subfolder=["models", "models"],
    weight_name=["ip-adapter_sd15.bin", "ip-adapter-plus_sd15.bin"],
)
pipe.set_ip_adapter_scale([0.7, 0.3])
```

Rules:

- State dicts must contain `image_proj` and `ip_adapter` sections.
- List lengths for paths, `subfolder`, and `weight_name` must match.
- Scale length must match the number of loaded IP-Adapters.
- Use `image_encoder_folder=None` when the workflow supplies `ip_adapter_image_embeds` or a FaceID variant without an image encoder.
- For video pipelines, load IP-Adapter before `enable_model_cpu_offload()` so the image encoder is not offloaded too early.
- `unload_ip_adapter()` removes IP-Adapter processors and related image encoder/feature extractor state where supported.

## IP-Adapter Plus, FaceID, And Masks

- Plus variants often require a compatible CLIP vision encoder such as `CLIPVisionModelWithProjection` supplied to the pipeline before loading weights.
- FaceID variants use face embeddings from InsightFace-like tooling and may require `image_encoder_folder=None` plus precomputed embeds.
- FaceID variants can include extra LoRA weights; diagnose PEFT availability when those loads fail.
- Masked IP-Adapter workflows use `IPAdapterMaskProcessor` to preprocess masks and pass masks through `cross_attention_kwargs` or the family-specific API expected by the pipeline.

## T2I-Adapter

Use T2I-Adapter when the user has a control image and an adapter trained to map that control signal into the base model.

```python
adapter = T2IAdapter.from_pretrained(t2i_adapter_dir, torch_dtype=torch.float16)
pipe = StableDiffusionXLAdapterPipeline.from_pretrained(
    base_model_dir,
    adapter=adapter,
    torch_dtype=torch.float16,
).to("cuda")
image = pipe(
    prompt,
    image=control_image,
    adapter_conditioning_scale=0.7,
).images[0]
```

For multiple controls:

```python
adapters = MultiAdapter([canny_adapter, depth_adapter])
pipe = StableDiffusionXLAdapterPipeline.from_pretrained(base_model_dir, adapter=adapters, torch_dtype=torch.float16)
image = pipe(prompt, image=[canny_image, depth_image], adapter_conditioning_scale=[0.7, 0.7]).images[0]
```

Rules:

- The number and order of control images must match the `MultiAdapter` order.
- `adapter_conditioning_scale` can be a float for one adapter or a list for multiple adapters.
- T2I-Adapter weights are loaded as `T2IAdapter` components, not with LoRA or IP-Adapter loaders.

## ControlNet Component Loading

Use ControlNet when the user needs structural controls through a ControlNet-specific pipeline.

```python
controlnet = ControlNetModel.from_pretrained(controlnet_dir, torch_dtype=torch.float16)
pipe = StableDiffusionXLControlNetPipeline.from_pretrained(
    base_model_dir,
    controlnet=controlnet,
    torch_dtype=torch.float16,
).to("cuda")
image = pipe(
    prompt,
    control_image=condition_image,
    controlnet_conditioning_scale=0.5,
).images[0]
```

Rules:

- Match the ControlNet class and checkpoint family to the base pipeline family: SD, SDXL, SD3, Flux, Hunyuan-DiT, etc.
- Control image argument names vary by pipeline (`control_image`, `image`, or family-specific names); inspect the selected pipeline call signature when coding.
- Multiple ControlNets require a multi-control wrapper or family-specific multi-control class plus a matching list of conditioning images/scales.
- ControlNet components can be passed into `from_single_file` pipeline loading when the base checkpoint is a single-file model.

## Single-File Pipeline Loading

Use `from_single_file` when the user has a `.safetensors`, `.ckpt`, `.gguf`, or other single checkpoint instead of a Diffusers multi-folder model.

```python
pipe = StableDiffusionXLPipeline.from_single_file(
    checkpoint_path,
    config=local_config_dir,
    torch_dtype=torch.float16,
    local_files_only=True,
)
```

For ControlNet single-file pipelines:

```python
controlnet = ControlNetModel.from_pretrained(controlnet_dir, torch_dtype=torch.float16, local_files_only=True)
pipe = StableDiffusionXLControlNetPipeline.from_single_file(
    checkpoint_path,
    controlnet=controlnet,
    config=local_config_dir,
    safety_checker=None,
    local_files_only=True,
)
```

Rules:

- Prefer `config=<local Diffusers config directory or repo id>` for reliable component configs, especially offline.
- Do not pass both `config` and `original_config` to model-level `from_single_file`.
- Use `original_config` for legacy original-layout conversion only when a Diffusers config is unavailable.
- If local configs are absent and `local_files_only=True`, load may fail; use a local config directory or allow one online cache-populating run if the user permits downloads.
- Pipeline-level GGUF single-file loading is not the documented path; load supported GGUF model classes with `from_single_file` and assemble the pipeline.

Generate a local-only skeleton with:

```bash
python scripts/single_file_loader_template.py --pipeline StableDiffusionXLControlNetPipeline --checkpoint ./model.safetensors --config ./config --controlnet ./controlnet --local-files-only
```
