# Component API Reference

This reference is for future agents using LTX-Video Python components directly. It distills component behavior from the package APIs, source flow, and lightweight installed-package inspection. It is not a CLI guide; route normal generation commands to `../local-inference/SKILL.md` and YAML/model choices to `../model-configs/SKILL.md`.

## Imports

```python
import torch

from ltx_video.pipelines.pipeline_ltx_video import (
    ConditioningItem,
    LTXMultiScalePipeline,
    LTXVideoPipeline,
)
from ltx_video.schedulers.rf import RectifiedFlowScheduler
from ltx_video.models.autoencoders.causal_video_autoencoder import CausalVideoAutoencoder
from ltx_video.models.autoencoders.latent_upsampler import LatentUpsampler
from ltx_video.models.transformers.transformer3d import Transformer3DModel
from ltx_video.models.transformers.symmetric_patchifier import SymmetricPatchifier
from ltx_video.utils.skip_layer_strategy import SkipLayerStrategy
from ltx_video.utils.prompt_enhance_utils import generate_cinematic_prompt
```

A direct `LTXVideoPipeline` instance must be assembled with compatible tokenizer, text encoder, transformer, scheduler, VAE, patchifier, and optional prompt enhancer models. If a user simply wants to run LTX-Video, prefer the repo's higher-level inference path through `../local-inference/SKILL.md`.

## `LTXVideoPipeline.__call__` signature

Verified call signature:

```python
LTXVideoPipeline.__call__(
    height,
    width,
    num_frames,
    frame_rate,
    prompt=None,
    negative_prompt='',
    num_inference_steps=20,
    skip_initial_inference_steps=0,
    skip_final_inference_steps=0,
    timesteps=None,
    guidance_scale=4.5,
    cfg_star_rescale=False,
    skip_layer_strategy=None,
    skip_block_list=None,
    stg_scale=1.0,
    rescaling_scale=0.7,
    guidance_timesteps=None,
    num_images_per_prompt=1,
    eta=0.0,
    generator=None,
    latents=None,
    prompt_embeds=None,
    prompt_attention_mask=None,
    negative_prompt_embeds=None,
    negative_prompt_attention_mask=None,
    output_type='pil',
    return_dict=True,
    callback_on_step_end=None,
    conditioning_items=None,
    decode_timestep=0.0,
    decode_noise_scale=None,
    mixed_precision=False,
    offload_to_cpu=False,
    enhance_prompt=False,
    text_encoder_max_tokens=256,
    stochastic_sampling=False,
    media_items=None,
    tone_map_compression_ratio=0.0,
    **kwargs,
)
```

Important `**kwargs` observed in the pipeline/inference path:

- `is_video=True` for video-shaped generation. If omitted or false, the pipeline treats temporal VAE scale as image-like.
- `vae_per_channel_normalize=True` when using checkpoints that include per-channel statistics.
- `image_cond_noise_scale=<float>` to add timestep-dependent noise to hard-conditioning latents.
- `device=<device>` is passed by the high-level inference helper, but direct component behavior primarily follows the pipeline's execution device and module devices.

Return behavior:

- With `return_dict=True`, returns a Diffusers `ImagePipelineOutput` whose `images` member is the output.
- `output_type='latent'` returns unpatchified latents in `images` with shape `(B, C, F_latent, H_latent, W_latent)` and does not VAE-decode.
- Non-latent output applies `tone_map_latents(...)`, VAE decode, and image-processor postprocess. The inference helper commonly uses `output_type='pt'` and crops padded tensors afterward.
- With `return_dict=False`, returns a one-element tuple `(image_or_latents,)`.

## Direct call checklist

Before calling the pipeline directly, check:

1. `height` and `width` are divisible by 8. The high-level inference wrapper pads to multiples of 32 for LTX workflows, but the direct pipeline input gate only checks divisibility by 8.
2. Exactly one prompt source is supplied:
   - either `prompt` or `prompt_embeds`;
   - if `prompt_embeds` is supplied, also supply `prompt_attention_mask`;
   - if `negative_prompt_embeds` is supplied, also supply `negative_prompt_attention_mask`;
   - direct positive and negative embeds/masks must have matching shapes.
3. If `skip_initial_inference_steps > 0`, provide `latents` or `media_items`; initial skip is intended for image/video-to-video continuation rather than pure text-to-video noise.
4. Do not pass both `latents` and `media_items`.
5. If `latents` or `media_items` is supplied, the first effective timestep must be `< 1.0`, otherwise the input would be replaced by pure noise and the code asserts.
6. If using spatiotemporal guidance, supply a valid `SkipLayerStrategy` value and a `skip_block_list` compatible with the transformer layer count.
7. If `enhance_prompt=True`, all four prompt-enhancer components must be initialized on the pipeline; this may require large model loads and should not be done as a component smoke.
8. For video conditioning masks, direct pipeline code asserts `num_images_per_prompt == 1`.

## Latents and media input contracts

### `prepare_latents`

Verified signature:

```python
LTXVideoPipeline.prepare_latents(
    latents,
    media_items,
    timestep,
    latent_shape,
    dtype,
    device,
    generator,
    vae_per_channel_normalize=True,
)
```

Behavior:

- Asserts `not (latents is not None and media_items is not None)`.
- Asserts that if input `latents` or `media_items` are provided, `timestep < 1.0`.
- A list of generators must have length equal to the effective batch size `latent_shape[0]`.
- If `media_items` is provided, it is encoded through the VAE and normalized according to `vae_per_channel_normalize`.
- If `latents` is provided, its shape must exactly equal `latent_shape`.
- Noise is sampled in patchified order and rearranged to `(B, C, F, H, W)`; returned shape is exactly `latent_shape`.
- Existing latents are mixed with noise as `timestep * noise + (1 - timestep) * latents`.

Typical direct video latent shape:

```python
latent_height = height // pipeline.vae_scale_factor
latent_width = width // pipeline.vae_scale_factor
latent_num_frames = num_frames // pipeline.video_scale_factor
if isinstance(pipeline.vae, CausalVideoAutoencoder) and is_video:
    latent_num_frames += 1
latent_shape = (
    batch_size * num_images_per_prompt,
    pipeline.transformer.config.in_channels,
    latent_num_frames,
    latent_height,
    latent_width,
)
```

`media_items` tensors are image/video tensors in channel-first format. Video media and conditioning media use shape `(B, 3, F, H, W)` and are expected to be scaled like the rest of the LTX inference path.

## Conditioning items

Verified dataclass signature:

```python
ConditioningItem(
    media_item,
    media_frame_number,
    conditioning_strength,
    media_x=None,
    media_y=None,
)
```

Fields:

- `media_item`: `torch.Tensor` with shape `(B, 3, F, H, W)`.
- `media_frame_number`: target start frame in the generated video.
- `conditioning_strength`: float strength, where `1.0` is hard conditioning and values between 0 and 1 are soft blends.
- `media_x`, `media_y`: optional target-frame top-left placement in pixels for spatial conditioning.

### `prepare_conditioning`

Verified signature:

```python
LTXVideoPipeline.prepare_conditioning(
    conditioning_items,
    init_latents,
    num_frames,
    height,
    width,
    vae_per_channel_normalize=False,
    generator=None,
)
```

Returns:

```python
init_latents, init_pixel_coords, conditioning_mask, num_cond_latents
```

Return contracts:

- `init_latents` is patchified to token shape `(B, N, C_token)` before return.
- `init_pixel_coords` is a coordinate tensor for the tokens, derived from latent coordinates and VAE temporal/spatial scale.
- `conditioning_mask` is `None` when there are no conditioning items; otherwise it has token-level strengths.
- `num_cond_latents` is the count of extra conditioning tokens prepended for non-first conditioning and must be stripped before final unpatchify/decode.

Assertions and shape rules:

- The pipeline VAE must be `CausalVideoAutoencoder`.
- Conditioning media must be rank 5: `(B, C, F, H, W)`.
- Conditioning sequence frame count must satisfy `F % 8 == 1`.
- `media_frame_number >= 0` and `media_frame_number + F <= num_frames`.
- If the conditioning item is not placed at frame 0, a multi-frame sequence start must align to a multiple of 8 because the latent temporal factor is 8.
- If conditioning dimensions differ from target dimensions, this is only allowed when `media_frame_number == 0` so the item can be resized/cropped into the target field.
- Spatial `media_x`/`media_y` means the user must provide `media_item` at the target size; the helper refuses to resize spatial-conditioning items.
- For spatial placement, item height/width must fit inside target height/width and be divisible by the VAE spatial scale.

### `trim_conditioning_sequence`

Verified signature:

```python
LTXVideoPipeline.trim_conditioning_sequence(start_frame, sequence_num_frames, target_num_frames)
```

It trims a sequence to fit in the target video and rounds down to `N * video_scale_factor + 1` frames. Use this before loading conditioning videos if the raw conditioning clip is longer than the remaining target duration.

## Skip-layer strategy and STG

Enum values:

```python
SkipLayerStrategy.AttentionSkip
SkipLayerStrategy.AttentionValues
SkipLayerStrategy.Residual
SkipLayerStrategy.TransformerBlock
```

The high-level inference helper maps config strings as follows:

| String aliases | Enum |
| --- | --- |
| `stg_av`, `attention_values` | `SkipLayerStrategy.AttentionValues` |
| `stg_as`, `attention_skip` | `SkipLayerStrategy.AttentionSkip` |
| `stg_r`, `residual` | `SkipLayerStrategy.Residual` |
| `stg_t`, `transformer_block` | `SkipLayerStrategy.TransformerBlock` |

`skip_block_list` can be a single list of block indices applied to all timesteps, or a list of lists selected through `guidance_timesteps`. The transformer creates a mask with shape `(num_layers, batch_size * num_conds)` and zeroes selected layer/batch positions for the perturbed STG branch. Invalid block indices surface as indexing errors; check `len(pipeline.transformer.transformer_blocks)` first.

## Prompt enhancement helpers

Main helper:

```python
generate_cinematic_prompt(
    image_caption_model,
    image_caption_processor,
    prompt_enhancer_model,
    prompt_enhancer_tokenizer,
    prompt,
    conditioning_items=None,
    max_new_tokens=256,
) -> list[str]
```

Behavior:

- With no conditioning, uses a text-to-video cinematic system prompt.
- With conditioning, only supports a single conditioning item at `media_frame_number == 0`; otherwise it logs a warning and returns the original prompts.
- For image-to-video enhancement, it extracts the first frame from each conditioning tensor and requires the number of first frames to match the number of prompts.
- `tensor_to_pil` asserts the conditioning tensor values are in `[-1, 1]` before converting to PIL.
- These helpers call model `.generate(...)`; do not use them for no-download/no-generation component smoke unless the user already loaded the prompt-enhancer models and accepts the cost.

## `tone_map_latents`

Verified signature:

```python
LTXVideoPipeline.tone_map_latents(latents, compression)
```

Behavior:

- `compression` must be in `[0, 1]`.
- `0.0` is identity; higher values apply sigmoid-based dynamic range compression.
- Shape is preserved for any latent tensor shape.
- In the pipeline call it is applied just before VAE decode when `output_type != 'latent'`.

## `LTXMultiScalePipeline`

Verified signature:

```python
LTXMultiScalePipeline.__call__(downscale_factor, first_pass, second_pass, *args, **kwargs)
```

Construction:

```python
multi = LTXMultiScalePipeline(video_pipeline, latent_upsampler)
```

Behavior:

1. Saves original `height`, `width`, and `output_type` from `kwargs`.
2. Computes low-resolution dimensions as `int(original * downscale_factor)` rounded down to a multiple of `video_pipeline.vae_scale_factor`.
3. Runs the wrapped `LTXVideoPipeline` first pass with `output_type='latent'` and `first_pass` overrides.
4. Unnormalizes latents, applies `LatentUpsampler`, normalizes latents again, and applies AdaIN filtering against the low-resolution latents.
5. Runs the wrapped pipeline second pass with `latents=<upsampled_latents>`, doubled low-resolution dimensions, original output type, and `second_pass` overrides.
6. If original output type was not `latent`, resizes output tensor back to original `height`/`width`.

Gotchas:

- `kwargs` must include `output_type`, `width`, and `height`; this class reads them directly.
- The latent upsampler must be on the same device as the latents.
- Multi-scale requires a compatible spatial upscaler checkpoint; a component smoke without that checkpoint cannot verify full multi-scale generation.
- YAML config selection and missing `spatial_upscaler_model_path` are handled in `../model-configs/SKILL.md`.

## Minimal direct-component snippets

### Scheduler-only smoke

```python
import torch
from ltx_video.schedulers.rf import RectifiedFlowScheduler

scheduler = RectifiedFlowScheduler(sampler="LinearQuadratic")
latents = torch.randn(2, 16, 8)
noise_pred = torch.randn_like(latents)
scheduler.set_timesteps(num_inference_steps=4, samples_shape=latents.shape)
out = scheduler.step(noise_pred, scheduler.timesteps[0], latents, return_dict=False)[0]
assert out.shape == latents.shape
```

### Demo VAE config check without weights

```python
from ltx_video.models.autoencoders.causal_video_autoencoder import (
    CausalVideoAutoencoder,
    create_video_autoencoder_demo_config,
)

vae = CausalVideoAutoencoder.from_config(create_video_autoencoder_demo_config(latent_channels=16))
assert vae.is_video_supported
print(vae.spatial_downscale_factor, vae.temporal_downscale_factor)  # demo config: 32, 8
```

These snippets verify component import/config/math surfaces only. They do not verify text encoder loading, checkpoint metadata, transformer/VAE checkpoint weights, prompt enhancement, image/video quality, or full generation.
