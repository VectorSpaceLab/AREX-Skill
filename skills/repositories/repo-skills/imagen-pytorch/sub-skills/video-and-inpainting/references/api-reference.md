# Video and Inpainting API Reference

This reference captures the video/inpainting surface that future agents usually need. It omits generic text/image generation and trainer/checkpoint details handled by sibling sub-skills.

## Public imports

```python
from imagen_pytorch import Imagen, ElucidatedImagen, ImagenTrainer, NullUnet, Unet3D
```

`Unet3D` is the video U-Net. `Imagen` and `ElucidatedImagen` both support video-shaped cascades and inpainting. `ImagenTrainer` delegates sample/forward calls to the underlying model.

## Tensor layout

| Purpose | Shape |
| --- | --- |
| Image batch | `(batch, channels, height, width)` |
| Video batch | `(batch, channels, frames, height, width)` |
| Image inpaint mask | `(batch, height, width)` |
| Video inpaint mask, shared across frames | `(batch, height, width)` |
| Video inpaint mask, per frame | `(batch, frames, height, width)` |
| Conditioning video frames | `(batch, channels, frames, height, width)` |

Height and width are expected to be square for model training/forward calls. Sampling outputs use each cascade stage's configured `image_sizes`.

## `Unet3D(...)` constructor parameters

Commonly tuned parameters:

| Parameter | Meaning |
| --- | --- |
| `dim` | Base channel dimension. Source emits a warning if very small; realistic diffusion models often need large values. |
| `dim_mults=(1,2,4,8)` | Per-resolution channel multipliers. |
| `num_resnet_blocks=1` | Number of residual blocks per layer; can be a tuple matching depth. |
| `temporal_strides=1` | Temporal downsample/upsample strides inside the U-Net. Product becomes `total_temporal_divisor`; input frames must be divisible by it unless `ignore_time=True`. |
| `channels=3`, `channels_out=None` | Input/output data channels. Imagen casting aligns these with the parent model. |
| `lowres_cond=False` | Required for cascade upsamplers; parent Imagen/ElucidatedImagen casts first stage to `False` and later stages to `True`. |
| `cond_images_channels=0` | Enables image conditioning; use `cond_video_frames` instead for frame conditioning. |
| `cond_on_text=True`, `text_embed_dim=...`, `max_text_len=256` | Text-conditioning controls; parent model usually sets these. |
| `layer_attns`, `layer_cross_attns`, `attn_heads`, `attn_dim_head` | Spatial/text attention controls. |
| `time_causal_attn=True`, `ff_time_token_shift=True` | Temporal attention/feedforward behavior. |
| `self_cond=False` | Self-conditioning support. |
| `resize_mode='nearest'` | Resize interpolation for conditioning inputs. |

Other constructor parameters are architectural knobs and should be treated like advanced model-design choices rather than runtime flags.

## `Unet3D.forward(...)` video parameters

Signature-relevant subset:

```python
unet(
    x, time,
    lowres_cond_img=None,
    lowres_noise_times=None,
    text_embeds=None,
    text_mask=None,
    cond_images=None,
    cond_video_frames=None,
    post_cond_video_frames=None,
    self_cond=None,
    cond_drop_prob=0.,
    ignore_time=False,
)
```

Rules:

- `x` must be 5D `(batch, channels, frames, height, width)`.
- Unless `ignore_time=True`, `x.shape[2]` must be divisible by `unet.total_temporal_divisor`.
- `cond_video_frames` and `post_cond_video_frames` are prepended/appended along the frame dimension, resized spatially to `x.shape[-1]`, and removed from the output before return.
- Conditioning-frame lengths must be divisible by `unet.total_temporal_divisor`.
- `cond_images` must stay 4D; use `cond_video_frames` for video-frame prompts.

## `Imagen(...)` and `ElucidatedImagen(...)` video constructor parameters

Shared video-relevant parameters:

| Parameter | Meaning |
| --- | --- |
| `unets=(...)` | Include `Unet3D` stages for video. If any stage is `Unet3D`, the model marks itself as video. |
| `image_sizes=(...)` | Cascade spatial sizes. Length must equal number of U-Nets. |
| `random_crop_sizes=(None, ...)` | Base stage crop must be `None`; upsamplers may crop. |
| `temporal_downsample_factor=1` | Int or tuple per stage. Cast to one value per U-Net. Must be descending and end in `1`. |
| `resize_cond_video_frames=True` | If true, conditioning videos are temporally scaled per cascade stage using that stage's downsample factor. |
| `resize_mode='nearest'` | Spatial/video interpolation mode for resizing internal images/videos/masks. |
| `condition_on_text=True` | If true, sampling/forward requires text strings or text embeddings. |
| `auto_normalize_img=True` | Inputs in `[0,1]` are normalized internally to `[-1,1]` and outputs unnormalized. |

`Imagen` additionally exposes diffusion schedule options such as `timesteps`, `noise_schedules`, and `pred_objectives`. `ElucidatedImagen` exposes Karras-style sampling/training parameters such as `num_sample_steps`, `sigma_min`, `sigma_max`, `rho`, `P_mean`, and related fields.

## `Imagen.sample(...)` video/inpainting parameters

Video/inpainting subset:

```python
imagen.sample(
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
    cond_scale=1.,
    start_at_unet_number=1,
    start_image_or_video=None,
    stop_at_unet_number=None,
    return_all_unet_outputs=False,
    return_pil_images=False,
    use_tqdm=True,
    use_one_unet_in_gpu=True,
)
```

Key behavior:

- Text-conditioned models use text batch size as `batch_size`.
- `inpaint_videos` is internally treated as `inpaint_images` and sets `video_frames` from `inpaint_videos.shape[2]` for video models.
- For video models without inpainting, pass `video_frames` explicitly.
- If a video mask is 3D, it is repeated across the inferred frame count; if 4D, `mask.shape[1]` must equal the video frame count.
- `return_pil_images=True` is invalid for video models.
- Sampling through a `NullUnet` stage asserts; use `NullUnet` only as a placeholder and skip it appropriately in image workflows, not ordinary video sampling.

## `ElucidatedImagen.sample(...)` differences

ElucidatedImagen has the same video/inpainting behavior, with additional `sigma_min` and `sigma_max` sample-time overrides and slightly different argument ordering:

```python
elucidated.sample(
    texts=None,
    text_masks=None,
    text_embeds=None,
    cond_images=None,
    cond_video_frames=None,
    post_cond_video_frames=None,
    inpaint_videos=None,
    inpaint_images=None,
    inpaint_masks=None,
    inpaint_resample_times=5,
    init_images=None,
    skip_steps=None,
    sigma_min=None,
    sigma_max=None,
    video_frames=None,
    batch_size=1,
    cond_scale=1.,
    start_at_unet_number=1,
    start_image_or_video=None,
    stop_at_unet_number=None,
    return_all_unet_outputs=False,
    return_pil_images=False,
    use_tqdm=True,
    use_one_unet_in_gpu=True,
)
```

The video-specific assertions and mask behavior match Imagen.

## Training/forward video parameters

Calling the parent model or trainer for training accepts `images` that may be image or video shaped:

```python
loss = trainer(videos, texts=texts, unet_number=1, ignore_time=False)
loss = trainer(images, texts=texts, unet_number=1)  # image-only pretraining path for Unet3D
```

Rules:

- For video models, 4D image input is reshaped to a single-frame video and `ignore_time=True` is set automatically.
- For 5D video input, `ignore_time=False` keeps temporal convolutions/attention active; setting it to `True` bypasses temporal operations.
- For cascades, `temporal_downsample_factor` computes each stage's target frame count, just as `image_sizes` computes spatial targets. This derivation still runs for the single-frame image-pretraining path, so factors greater than 1 can fail before temporal modules are skipped.
