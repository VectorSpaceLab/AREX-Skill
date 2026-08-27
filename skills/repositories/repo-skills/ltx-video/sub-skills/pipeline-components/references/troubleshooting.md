# Pipeline Component Troubleshooting

Use this when direct `LTXVideoPipeline`, scheduler, VAE, transformer, latent upsampler, prompt-enhancement, or conditioning calls fail. If the user is running the CLI or `infer(...)`, route to `../local-inference/SKILL.md`. If the failure is about choosing a YAML/model config, route to `../model-configs/SKILL.md`.

## Quick triage

1. Is this a normal end-user generation task? If yes, use `../local-inference/SKILL.md` rather than wiring components manually.
2. Is a YAML field or model family wrong? If yes, use `../model-configs/SKILL.md`.
3. Is the user trying to prove installation/import/component math without downloads? Run `../scripts/check_components.py --scheduler --vae-config`.
4. Is the user claiming full checkpoint inference based only on component smoke? Correct that claim: component smokes do not verify full generation.

## Shape and divisibility problems

### `height` and `width` divisibility

Error pattern:

```text
`height` and `width` have to be divisible by 8 ...
```

Cause: `LTXVideoPipeline.check_inputs` rejects non-multiples of 8. The high-level inference workflow pads to multiples of 32, but the direct class call does not pad for you.

Fix:

```python
height = ((height - 1) // 32 + 1) * 32
width = ((width - 1) // 32 + 1) * 32
```

Use multiples of 32 for LTX-style video generation unless there is a specific reason to call the lower-level pipeline at another multiple of 8.

### Latent shape mismatch

Error pattern:

```text
Latents have to be of shape ... but are ...
```

Cause: direct `latents` must match the pipeline-computed latent shape exactly:

```python
(
    batch_size * num_images_per_prompt,
    pipeline.transformer.config.in_channels,
    latent_num_frames,
    height // pipeline.vae_scale_factor,
    width // pipeline.vae_scale_factor,
)
```

For video with `CausalVideoAutoencoder`, `latent_num_frames = num_frames // pipeline.video_scale_factor + 1`. If `is_video` is omitted, `video_scale_factor` is treated as 1 inside the call and the expected frame count changes.

Fixes:

- Pass `is_video=True` for video tensors.
- Use the transformer's configured `in_channels` rather than guessing 4/64/128.
- Recompute latent shape after padding height/width/frame count.
- If using a custom VAE, inspect `pipeline.vae_scale_factor` and `pipeline.video_scale_factor`.

### Media tensor rank or channel error

Patterns:

```text
assert media_item.ndim == 5
Expects tensors with 3 channels, got ...
```

Fix: use channel-first video media shaped `(B, 3, F, H, W)`. Images used as conditioning are still represented as video tensors with `F=1`.

## Prompt and embedding conflicts

Error patterns:

```text
Cannot forward both `prompt` and `prompt_embeds`
Provide either `prompt` or `prompt_embeds`
Must provide `prompt_attention_mask` when specifying `prompt_embeds`
`prompt_embeds` and `negative_prompt_embeds` must have the same shape
```

Fix:

- Use exactly one positive prompt source: raw `prompt` or precomputed `prompt_embeds`.
- If using embeds, pass the matching attention mask.
- If using negative embeds, pass `negative_prompt_attention_mask` too.
- Positive and negative embed tensors and masks must have identical shapes.
- Do not pass raw `negative_prompt` together with `negative_prompt_embeds`.

## `latents` + `media_items` assertion

Error pattern:

```text
Cannot provide both latents and media_items. Please provide only one of the two.
```

Cause: `prepare_latents` treats both as alternative initial latent sources.

Fix:

- Use `media_items` for img2img/vid2vid-style encoding through the VAE.
- Use `latents` when you already have correctly shaped latents, such as from a multi-scale first pass or custom latent editing.
- Do not supply both. If you need to modify encoded media latents manually, encode media first, modify latents, then call with only `latents`.

## Input latents/media at timestep 1.0

Error pattern:

```text
Input media_item or latents are provided, but they will be replaced with noise.
```

Cause: input latents/media are only meaningful when the initial timestep is `< 1.0`.

Fix:

- Use `skip_initial_inference_steps > 0` with a valid schedule so the first effective timestep is below 1.
- Or pass explicit `timesteps` whose first value is below 1.
- Do not use pure text-to-video settings while also expecting `latents`/`media_items` to survive.

## Invalid skip steps

Error pattern:

```text
invalid skip inference step values: must be non-negative and the sum ... less than the number of inference steps
```

Cause: `skip_initial_inference_steps` or `skip_final_inference_steps` is negative, or their sum is at least `num_inference_steps`.

Fix:

```python
assert skip_initial_inference_steps >= 0
assert skip_final_inference_steps >= 0
assert skip_initial_inference_steps + skip_final_inference_steps < num_inference_steps
```

Additional assertion:

```text
skip_initial_inference_steps (...) is used for image-to-image/video-to-video - media_item or latents should be provided.
```

Fix: either set `skip_initial_inference_steps=0` for pure text-to-video, or provide exactly one of `latents` or `media_items`.

## Scheduler errors

### `set_timesteps` not called

Error pattern:

```text
Number of inference steps is 'None', you need to run 'set_timesteps' after creating the scheduler
```

Fix:

```python
scheduler.set_timesteps(num_inference_steps=20, samples_shape=latents.shape, device=latents.device)
```

For shifted schedules, pass a rank-3, rank-4, or rank-5 `samples_shape`.

### Both timesteps and num steps

Error pattern:

```text
You cannot provide both `timesteps` and `num_inference_steps`.
```

Fix: choose one. Explicit `timesteps` are useful for custom schedules; otherwise use `num_inference_steps`.

### Unsupported sample shape for shifting

Error pattern:

```text
Samples must have shape (b, t, c), (b, c, h, w) or (b, c, f, h, w)
```

Fix: pass token latents `(B, N, C)` or image/video latents `(B, C, H, W)` / `(B, C, F, H, W)` to `samples_shape`.

## Conditioning sequence assertions

### Frame count must be `N * 8 + 1`

Pattern:

```text
assert n_frames % 8 == 1
```

Fix: trim or pad conditioning clips to `1, 9, 17, 25, ...` frames. Use `pipeline.trim_conditioning_sequence(start_frame, sequence_num_frames, target_num_frames)` to trim to an allowed length.

### Out-of-range conditioning sequence

Pattern:

```text
media_frame_number + n_frames <= num_frames
```

Fix: ensure the conditioning clip fits within the generated video. For a generated video of `num_frames=97`, a 17-frame conditioning clip can start no later than frame 80.

### Non-first sequence start alignment

Pattern:

```text
assert media_frame_number % 8 == 0
```

Cause: non-first conditioning sequences are inserted on latent temporal boundaries.

Fix: start non-first multi-frame conditioning at frame `8, 16, 24, ...`. Single-frame conditioning still creates extra conditioning tokens, but the direct conditioning path remains strict about sequence handling.

### Spatial conditioning resize error

Pattern:

```text
Provide media_item in the target size for spatial conditioning.
```

Cause: `media_x` or `media_y` is set; the helper will not resize/crop spatial-conditioning tensors.

Fix: pre-process the conditioning tensor to the target generation size before building `ConditioningItem(media_x=..., media_y=...)`.

### Spatial placement out of bounds or not divisible

Patterns:

```text
Conditioning item size ... is larger than target size ...
Conditioning item ... is out of bounds ...
assert h % scale == 0 and w % scale == 0
```

Fix:

- Ensure `media_x + item_width <= target_width` and `media_y + item_height <= target_height`.
- Ensure conditioning item H/W are divisible by `pipeline.vae_scale_factor`.
- If the item does not touch a target border, the implementation strips one latent border before insertion; account for possible one-latent shrink in advanced diagnostics.

## Skip-layer and STG failures

Symptoms:

- Indexing errors in `create_skip_layer_mask`.
- No visible effect from STG.
- Shape differences when some timesteps enable STG/CFG and others do not.

Fixes:

- Use a valid enum: `SkipLayerStrategy.AttentionValues`, `AttentionSkip`, `Residual`, or `TransformerBlock`.
- Ensure every block index in `skip_block_list` is in `range(len(transformer.transformer_blocks))`.
- Keep `stg_scale`, `guidance_scale`, and `rescaling_scale` shapes consistent with `guidance_timesteps` when supplying lists.
- For compiled/graph-captured execution, avoid changing STG/CFG on/off across timesteps; the source notes that different timestep branches can create different input shapes.

## Prompt enhancement errors

Patterns:

```text
Image caption model must be initialized if enhance_prompt is True
Text prompt enhancer model must be initialized if enhance_prompt is True
Number of conditioning frames must match number of prompts
```

Fixes:

- If `enhance_prompt=False`, no prompt-enhancer models are needed.
- If `enhance_prompt=True`, initialize all four components: image-caption model, image-caption processor, LLM model, LLM tokenizer.
- Prompt enhancement with conditioning only supports one conditioning item at frame 0. Multiple or non-first conditioning returns original prompts with a warning.
- Conditioning tensors converted to PIL must have values in `[-1, 1]`.

## Checkpoint metadata and config mapping

### Single `.safetensors` metadata

Direct component loaders expect the safetensors metadata key `config`:

- Scheduler: JSON contains `scheduler`.
- VAE: JSON contains `vae`.
- Transformer: JSON contains `transformer`.
- Latent upsampler: metadata config is the upsampler config itself.

If metadata is missing or malformed, loading fails. This is not fixed by changing the pipeline call; use a supported LTX checkpoint or provide a proper config/state-dict pair.

### Diffusers directory mapping

Diffusers-style directories must match the built-in config mapping. Unmapped newer or custom configs may fail with messages such as:

```text
Provided diffusers checkpoint config for VAE is not suppported.
Provided diffusers checkpoint config for transformer is not suppported.
```

Fix: use a known Lightricks/LTX-Video checkpoint layout, convert the checkpoint with a verified mapping, or route model-choice/config questions to `../model-configs/SKILL.md`.

## FP8 / Q8 kernels error

Error pattern:

```text
Q8-Kernels not found. To use FP8 checkpoint, please install Q8 kernels ...
```

Cause: FP8 configs call the transformer creation path that imports `q8_kernels.integration.patch_transformer`.

Fix options:

- Use a bfloat16/non-FP8 config if the user does not need FP8.
- Install the external LTXVideo-Q8-Kernels package only when the user's accelerator and environment support it.
- Do not treat scheduler/VAE component smoke as proof that FP8 transformer inference works.

## CUDA, MPS, and CPU dtype/device issues

Common patterns:

- CUDA unavailable even though a GPU is expected.
- MPS operations missing or dtype unsupported.
- CPU bfloat16 operations are slow or unsupported for some model paths.
- Mixed device errors between latents, VAE, transformer, text encoder, scheduler timesteps, and latent upsampler.

Fixes:

- Run `../scripts/check_components.py --scheduler --vae-config --cuda-smoke` to separate package import/config issues from CUDA availability.
- Put all loaded pipeline modules on the intended device before generation.
- For direct scheduler tests, pass `device=latents.device` to `set_timesteps`.
- For prompt/text models, ensure embeds and masks are moved to the pipeline execution device.
- Use `mixed_precision=True` only when the target device supports the autocast dtype used by the pipeline (`bfloat16`).
- `offload_to_cpu=True` only helps on CUDA paths; high-level inference warns and disables it when already on CPU.

## Multi-scale upscaler problems

Patterns:

```text
spatial upscaler model path is missing ... required for multi-scale rendering
assert latents.device == latest_upsampler.device
KeyError: 'output_type' / 'width' / 'height'
```

Fixes:

- Multi-scale config selection and `spatial_upscaler_model_path` belong in `../model-configs/SKILL.md`.
- When using `LTXMultiScalePipeline` directly, include `output_type`, `width`, and `height` in `kwargs`.
- Move `latent_upsampler` to the same device as the wrapped video pipeline and latents.
- Ensure upsampler `in_channels` matches VAE/transformer latent channels.
- Remember that low-resolution dimensions are rounded down to multiples of `video_pipeline.vae_scale_factor`; tiny requested sizes or tiny `downscale_factor` can collapse dimensions.
- A no-download component smoke cannot validate a real latent upsampler checkpoint.

## Safe diagnostics script

Run from any environment where `ltx_video` is importable:

```bash
python skills/disco/ltx-video/sub-skills/pipeline-components/scripts/check_components.py --help
python skills/disco/ltx-video/sub-skills/pipeline-components/scripts/check_components.py --scheduler --vae-config
```

Optional CUDA check:

```bash
python skills/disco/ltx-video/sub-skills/pipeline-components/scripts/check_components.py --scheduler --device cuda --cuda-smoke
```

Expected successful signals include scheduler shape preservation and demo VAE downscale factors. These signals are intentionally small and do not prove full checkpoint generation.
