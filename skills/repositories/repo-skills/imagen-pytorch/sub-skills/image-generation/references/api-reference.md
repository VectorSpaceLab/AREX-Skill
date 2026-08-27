# Image API Reference

This reference is distilled for `imagen-pytorch` distribution version `2.1.0`. It is self-contained for future use; do not reopen the package source for the facts below.

## Public imports owned here

```python
from imagen_pytorch import (
    Unet, NullUnet, BaseUnet64, SRUnet256, SRUnet1024,
    Imagen, ElucidatedImagen,
)
```

Related but routed elsewhere: `ImagenTrainer`, config classes, checkpoint helpers, data/T5 helpers, CLI commands, and `Unet3D` video workflows.

## Tensor conventions

| Argument | Image-only shape / type | Notes |
|---|---|---|
| `images` for training | `(batch, channels, height, width)` | Height and width must be square. `Imagen` accepts float or half tensors; `ElucidatedImagen` asserts `torch.float`. With `auto_normalize_img=True`, inputs are expected in `[0, 1]`; `uint8` is cast to float / 255. |
| sampled output tensor | `(batch, channels, image_size, image_size)` | Default `channels=3`. Values are unnormalized back to `[0, 1]` when `auto_normalize_img=True`. |
| `text_embeds` | `(batch, sequence, text_embed_dim)` | Final dimension must match `Imagen(..., text_embed_dim=...)` / `ElucidatedImagen(..., text_embed_dim=...)`. Sequence length is commonly up to 256. |
| `text_masks` / `text_mask` | `(batch, sequence)` bool | Optional; if omitted, the package derives it from nonzero embedding rows. |
| `inpaint_images` | `(batch, channels, height, width)` | Batch must match `batch_size` or text batch. Pair with `inpaint_masks`. |
| `inpaint_masks` | `(batch, height, width)` bool-like | Must be supplied if and only if `inpaint_images` is supplied. Video mask variants belong to `video-and-inpainting`. |
| `cond_images` | `(batch, cond_images_channels, height, width)` | Only pass if the target `Unet` was constructed with matching `cond_images_channels > 0`. |
| `start_image_or_video` | low-resolution image batch | Required when `start_at_unet_number > 1`; for image workflows pass `(batch, channels, prev_size, prev_size)`. |

## `Unet`

Condensed constructor:

```python
Unet(
    *,
    dim,
    text_embed_dim=<default T5 encoded dim>,
    num_resnet_blocks=1,
    cond_dim=None,
    num_image_tokens=4,
    num_time_tokens=2,
    learned_sinu_pos_emb_dim=16,
    out_dim=None,
    dim_mults=(1, 2, 4, 8),
    cond_images_channels=0,
    channels=3,
    channels_out=None,
    attn_dim_head=64,
    attn_heads=8,
    ff_mult=2.0,
    lowres_cond=False,
    layer_attns=True,
    layer_attns_depth=1,
    layer_mid_attns_depth=1,
    layer_attns_add_text_cond=True,
    attend_at_middle=True,
    layer_cross_attns=True,
    use_linear_attn=False,
    use_linear_cross_attn=False,
    cond_on_text=True,
    max_text_len=256,
    init_dim=None,
    init_conv_kernel_size=7,
    init_cross_embed=True,
    init_cross_embed_kernel_sizes=(3, 7, 15),
    cross_embed_downsample=False,
    cross_embed_downsample_kernel_sizes=(2, 4),
    attn_pool_text=True,
    attn_pool_num_latents=32,
    dropout=0.0,
    memory_efficient=False,
    init_conv_to_final_conv_residual=False,
    use_global_context_attn=True,
    scale_skip_connection=True,
    final_resnet_block=True,
    final_conv_kernel_size=3,
    self_cond=False,
    resize_mode="nearest",
    combine_upsample_fmaps=False,
    pixel_shuffle_upsample=True,
)
```

Important construction notes:

- `attn_heads` must be greater than `1`; tiny smoke examples use `2`.
- If `cond_on_text=True`, `text_embed_dim` must exist and must match future `text_embeds.shape[-1]`.
- `layer_attns`, `layer_cross_attns`, `use_linear_attn`, `use_linear_cross_attn`, and `num_resnet_blocks` may be scalars or tuples matching the number of resolutions implied by `dim_mults`.
- `lowres_cond` is normally left alone. `Imagen` and `ElucidatedImagen` recast each unet so the first stage is not low-res-conditioned and later stages are low-res-conditioned.
- `cond_images_channels > 0` enables auxiliary image conditioning and then requires `cond_images` with exactly that channel count on forward/sample paths.

Useful methods:

- `unet.forward(x, time, *, lowres_cond_img=None, lowres_noise_times=None, text_embeds=None, text_mask=None, cond_images=None, self_cond=None, cond_drop_prob=0.0)`.
- `unet.forward_with_cond_scale(..., cond_scale=1.0, remove_parallel_component=True, keep_parallel_frac=0.0, **kwargs)` performs classifier-free guidance by comparing conditional and dropped-conditioning predictions.
- `unet.persist_to_file(path)` and `Unet.hydrate_from_file(path)` exist, but trainer/checkpoint flows should route to [training-and-checkpointing](../../training-and-checkpointing/SKILL.md).

## Predefined image unets

| Class | Defaults and intended use |
|---|---|
| `BaseUnet64` | Paper-style base generator: `dim=512`, `dim_mults=(1, 2, 3, 4)`, `num_resnet_blocks=3`, attention and cross-attention on the last three resolution levels, `attn_heads=8`, `memory_efficient=False`. CUDA-scale. |
| `SRUnet256` | Super-resolution/upscaler profile: `dim=128`, `dim_mults=(1, 2, 4, 8)`, `num_resnet_blocks=(2, 4, 8, 8)`, attention/cross-attention only at the final level, `attn_heads=8`, `memory_efficient=True`. |
| `SRUnet1024` | Larger upscaler profile: like `SRUnet256`, but `layer_attns=False` and cross-attention only at the final level. CUDA-scale and memory-heavy. |
| `NullUnet` | Placeholder stage for super-resolution-only branches. It returns its input, has no real diffusion capacity, and cannot be trained or sampled. |

## `Imagen`

Condensed constructor:

```python
Imagen(
    unets,
    *,
    image_sizes,
    text_encoder_name=<default T5 name>,
    text_embed_dim=None,
    channels=3,
    timesteps=1000,
    cond_drop_prob=0.1,
    loss_type="l2",
    noise_schedules="cosine",
    pred_objectives="noise",
    random_crop_sizes=None,
    lowres_noise_schedule="linear",
    lowres_sample_noise_level=0.2,
    per_sample_random_aug_noise_level=False,
    condition_on_text=True,
    auto_normalize_img=True,
    dynamic_thresholding=True,
    dynamic_thresholding_percentile=0.95,
    only_train_unet_number=None,
    temporal_downsample_factor=1,
    resize_cond_video_frames=True,
    resize_mode="nearest",
    min_snr_loss_weight=True,
    min_snr_gamma=5,
)
```

Constructor assertions and defaults:

- `len(unets) == len(image_sizes)` is required.
- `timesteps`, `pred_objectives`, `dynamic_thresholding`, `min_snr_loss_weight`, and `min_snr_gamma` may be scalars or per-unet tuples.
- `noise_schedules` defaults to cosine for the first two stages and linear for later upsamplers after padding to the cascade length.
- `random_crop_sizes` is per stage; the first entry must be `None` because base unet training should not randomly crop.
- Low-resolution conditioning must be `(False, True, True, ...)` across the cascade. The wrapper casts normal `Unet` instances into that pattern.
- `cond_drop_prob > 0` is required for meaningful classifier-free guidance with `cond_scale != 1`.
- `condition_on_text=False` makes the model unconditional; then do not pass `texts`, `text_embeds`, or `text_masks`.

Training call:

```python
loss = imagen(
    images,
    texts=None,
    text_embeds=None,
    text_masks=None,
    unet_number=None,
    cond_images=None,
    **kwargs,
)
```

Important training assertions:

- Images must be square and channel count must match `channels`.
- If the cascade has more than one unet, `unet_number` is mandatory.
- `NullUnet` stages cannot be trained.
- `images` dtype must be float or half.
- For text-conditioned models, provide non-empty `texts` or compatible `text_embeds`; text count must equal image batch when using strings.
- For unconditional models, passing `text_embeds` is an error.

Sampling call:

```python
images = imagen.sample(
    texts=None,
    text_masks=None,
    text_embeds=None,
    video_frames=None,
    cond_images=None,
    cond_video_frames=None,
    post_cond_video_frames=None,
    inpaint_videos=None,
    inpaint_images=None,
    inpaint_masks=None,
    inpaint_resample_times=5,
    init_images=None,
    skip_steps=None,
    batch_size=1,
    cond_scale=1.0,
    cfg_remove_parallel_component=True,
    cfg_keep_parallel_frac=0.0,
    lowres_sample_noise_level=None,
    start_at_unet_number=1,
    start_image_or_video=None,
    stop_at_unet_number=None,
    return_all_unet_outputs=False,
    return_pil_images=False,
    device=None,
    use_tqdm=True,
    use_one_unet_in_gpu=True,
)
```

Sampling notes:

- If `texts` are passed without `text_embeds`, the package encodes them through T5. Use precomputed embeddings to avoid that path.
- For text-conditioned sampling, `batch_size` is inferred from `text_embeds`.
- `cond_scale` can be a scalar or per-unet tuple. Use values above `1` only when the model was trained with nonzero `cond_drop_prob`; keep `1` for unconditional smoke checks.
- `start_at_unet_number > 1` requires `start_image_or_video` and skips earlier stages. This is the sampling path for upscaler-only training.
- `stop_at_unet_number` can stop the cascade early and must be at least `start_at_unet_number`.
- Sampling asserts when it reaches a `NullUnet`; therefore a `NullUnet` base is valid only if `start_at_unet_number` skips it.
- `return_pil_images=True` returns a list of PIL images for image models; automatic video-to-file conversion is not supported here.

## `ElucidatedImagen`

`ElucidatedImagen` uses the same unet cascade, image/text contracts, low-resolution conditioning pattern, `NullUnet` restrictions, inpainting pairing, `start_at_unet_number`, and `return_pil_images` behavior as `Imagen`, but replaces DDPM timestep/noise-schedule settings with Karras-style parameters.

Condensed constructor:

```python
ElucidatedImagen(
    unets,
    *,
    image_sizes,
    text_encoder_name=<default T5 name>,
    text_embed_dim=None,
    channels=3,
    cond_drop_prob=0.1,
    random_crop_sizes=None,
    resize_mode="nearest",
    temporal_downsample_factor=1,
    resize_cond_video_frames=True,
    lowres_sample_noise_level=0.2,
    per_sample_random_aug_noise_level=False,
    condition_on_text=True,
    auto_normalize_img=True,
    dynamic_thresholding=True,
    dynamic_thresholding_percentile=0.95,
    only_train_unet_number=None,
    lowres_noise_schedule="linear",
    num_sample_steps=32,
    sigma_min=0.002,
    sigma_max=80,
    sigma_data=0.5,
    rho=7,
    P_mean=-1.2,
    P_std=1.2,
    S_churn=80,
    S_tmin=0.05,
    S_tmax=50,
    S_noise=1.003,
)
```

Karras parameter notes:

- `num_sample_steps`, `sigma_min`, `sigma_max`, `sigma_data`, `rho`, `P_mean`, `P_std`, `S_churn`, `S_tmin`, `S_tmax`, and `S_noise` may be scalars or per-unet tuples.
- `sample(..., sigma_min=None, sigma_max=None, ...)` can override per-stage sigma bounds at sample time.
- `num_sample_steps` must be at least `2` for a valid schedule.
- `ElucidatedImagen.forward` asserts `images.dtype == torch.float`; avoid half inputs for this wrapper.

