# Inference API reference

This page records the verified runtime surface used by the DreamOmni2 CLI wrappers.

## Core pipeline

### `DreamOmni2Pipeline.__call__`

Verified signature:

```python
(self, images=None, prompt=None, prompt_2=None, negative_prompt=None, negative_prompt_2=None, true_cfg_scale=1.0, height=None, width=None, num_inference_steps=28, sigmas=None, guidance_scale=3.5, num_images_per_prompt=1, generator=None, latents=None, prompt_embeds=None, pooled_prompt_embeds=None, ip_adapter_image=None, ip_adapter_image_embeds=None, negative_ip_adapter_image=None, negative_ip_adapter_image_embeds=None, negative_prompt_embeds=None, negative_pooled_prompt_embeds=None, output_type='pil', return_dict=True, joint_attention_kwargs=None, callback_on_step_end=None, callback_on_step_end_tensor_inputs=['latents'], max_sequence_length=512, max_area=1024**2, _auto_resize=True)
```

Key points:

- `images` accepts a list of PIL images, numpy arrays, or tensors.
- `prompt` is the diffusion prompt produced by the VLM stage.
- `height` and `width` are most relevant to generation runs; editing generally follows the resized source image size.
- `guidance_scale` defaults to `3.5` in the repo scripts.
- `num_inference_steps` defaults to `30` in the bundled wrappers.
- `max_area` and `_auto_resize` let the pipeline choose a Kontext-compatible image size.

### Loader and adapter methods

The workflows use these methods from the Diffusers pipeline API:

- `DreamOmni2Pipeline.from_pretrained(base_model_path, torch_dtype=torch.bfloat16)`
- `pipe.load_lora_weights(adapter_path, adapter_name=...)`
- `pipe.set_adapters([adapter_name], adapter_weights=[1])`
- `pipe.to("cuda")`

## VLM stage

### `load_vlm_stack(vlm_path)`

The bundled helper loads:

- `Qwen2_5_VLForConditionalGeneration.from_pretrained(vlm_path, torch_dtype="bfloat16", device_map="cuda")`
- `AutoProcessor.from_pretrained(vlm_path)`

### `infer_vlm_prompt(vlm_model, processor, image_paths, instruction, prefix, device="cuda")`

This helper:

1. Builds a chat message with two image inputs and the instruction text.
2. Runs `processor.apply_chat_template(..., add_generation_prompt=True)`.
3. Loads and resizes the images with the Kontext bucket helper.
4. Calls `vlm_model.generate(..., do_sample=False, max_new_tokens=4096)`.
5. Decodes the result and normalizes the fenced response text.

## Shared helpers

### `resizeinput(img)`

- Resizes a PIL image to the nearest DreamOmni2/Kontext resolution bucket.
- Rounds the dimensions down to a multiple of 16.
- Used by both CLI and web workflows before the diffusion call.

### `load_and_resize_images(image_paths)`

- Loads each image path with the diffusers image loader.
- Applies the shared Kontext resize helper.

### `build_vlm_messages(image_paths, instruction, prefix)`

- Builds the Qwen2.5-VL message payload used by both workflows.
- Appends the task-specific prefix string to the instruction.

### `extract_vlm_text(text)`

- Strips a fenced VLM response when present.
- Falls back to trimmed plain text if the response is already unwrapped.

### `run_dreamomni2_workflow(...)`

Common wrapper used by the bundled CLI scripts:

- `mode="edit"` uses the editing LoRA and the source-image-first convention.
- `mode="generate"` uses the generation LoRA and explicit `height`/`width` values.
- Saves the resulting image to the requested output path.

## CLI expectations

- Editing CLI: two input images, source image first, instruction required.
- Generation CLI: two input images, instruction required, `height` and `width` optional with defaults of `1024`.
- Both workflows use the same VLM prompt stage and save a single output image.
