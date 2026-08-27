# Video and Inpainting Workflows

These recipes are distilled for future use without reopening the source checkout. They intentionally separate shape preflight from expensive generation or training.

## 1. Text-to-video with `Unet3D`

Use `Unet3D` for every video cascade stage. A model is treated as video-capable when any stage is a `Unet3D`, but mixing image and video stages is rarely useful and complicates shapes.

```python
import torch
from imagen_pytorch import Unet3D, ElucidatedImagen, ImagenTrainer

unet1 = Unet3D(dim=64, dim_mults=(1, 2, 4, 8))
unet2 = Unet3D(dim=64, dim_mults=(1, 2, 4, 8))

imagen = ElucidatedImagen(
    unets=(unet1, unet2),
    image_sizes=(16, 32),
    random_crop_sizes=(None, 16),
    temporal_downsample_factor=(2, 1),
    num_sample_steps=10,
    cond_drop_prob=0.1,
)
trainer = ImagenTrainer(imagen)

texts = ["a whale breaching", "fireworks over water"]
videos = torch.randn(2, 3, 10, 32, 32)  # (batch, channels, frames, height, width)

loss = trainer(videos, texts=texts, unet_number=1, ignore_time=False)
trainer.update(unet_number=1)

sampled = trainer.sample(texts=texts, video_frames=20, return_pil_images=False)
assert sampled.shape == (2, 3, 20, 32, 32)
```

Notes:

- `video_frames` is a sampling-time argument, not only a construction-time setting.
- With `temporal_downsample_factor=(2, 1)`, a 20-frame sample uses 10 frames at stage 1 and 20 frames at stage 2.
- Real training/generation is CUDA-scale and may be slow or memory-heavy; do not treat the recipe as a smoke test.

## 2. Image-only pretraining with `Unet3D`

A video model can be trained first on text-image pairs. If the model is video (`Unet3D`) and training input is 4D `(batch, channels, height, width)`, the Imagen/ElucidatedImagen forward path reshapes it to `(batch, channels, 1, height, width)` and sets `ignore_time=True`.

```python
images = torch.randn(2, 3, 32, 32)
texts = ["one still frame", "another still frame"]

loss = trainer(images, texts=texts, unet_number=1)
# Internally behaves like a single-frame video and bypasses temporal modules.
```

Use this only for pretraining or debugging still-image compatibility. When training on actual videos, pass 5D video tensors and choose `ignore_time=False` unless deliberately disabling temporal components. Even though temporal modules are ignored for 4D inputs, preflight a one-frame plan against `temporal_downsample_factor`; factors greater than 1 can still be incompatible with the source's frame-dimension derivation.

## 3. Video frame conditioning

Use `cond_video_frames` for preceding frames and `post_cond_video_frames` for following frames. Both are 5D videos in `(batch, channels, frames, height, width)` order.

```python
cond_video_frames = torch.randn(2, 3, 4, 32, 32)
post_cond_video_frames = torch.randn(2, 3, 2, 32, 32)

sampled = trainer.sample(
    texts=["continue the motion", "continue the motion"],
    video_frames=16,
    cond_video_frames=cond_video_frames,
    post_cond_video_frames=post_cond_video_frames,
    return_pil_images=False,
)
```

When `resize_cond_video_frames=True` (default), each cascade stage temporally downsamples conditioning frames according to its `temporal_downsample_factor`. Source logic requires conditioning-frame lengths to be divisible by the relevant downsample scale and by the receiving `Unet3D.total_temporal_divisor`.

If you set `resize_cond_video_frames=False`, you own the per-stage frame lengths and divisibility checks.

## 4. Image inpainting

Image inpainting works on Imagen or ElucidatedImagen via paired `inpaint_images` and `inpaint_masks`.

```python
inpaint_images = torch.randn(4, 3, 512, 512)          # (batch, channels, height, width)
inpaint_masks = torch.ones(4, 512, 512, dtype=torch.bool)  # (batch, height, width)

out = trainer.sample(
    texts=["prompt 1", "prompt 2", "prompt 3", "prompt 4"],
    inpaint_images=inpaint_images,
    inpaint_masks=inpaint_masks,
    cond_scale=5.0,
)
assert out.shape == (4, 3, 512, 512)
```

Rules:

- Pass images and masks together; exactly one of them is an assertion failure.
- Mask batch must match inpaint image batch and, for text-conditioned models, text batch.
- Masks are internally expanded to a channel dimension and resized to each stage resolution.

## 5. Video inpainting

Use `inpaint_videos`, not `inpaint_images`, for clarity when input is 5D video. The implementation maps `inpaint_videos` into the same internal variable as `inpaint_images`.

```python
inpaint_videos = torch.randn(4, 3, 8, 512, 512)       # (batch, channels, frames, height, width)
per_frame_masks = torch.ones(4, 8, 512, 512, dtype=torch.bool)

out = trainer.sample(
    texts=["prompt 1", "prompt 2", "prompt 3", "prompt 4"],
    inpaint_videos=inpaint_videos,
    inpaint_masks=per_frame_masks,
    cond_scale=5.0,
    return_pil_images=False,
)
assert out.shape == (4, 3, 8, 512, 512)
```

A shared mask can be passed as `(batch, height, width)`; the sample path broadcasts it across `inpaint_videos.shape[2]` frames.

## 6. Preflight-only shape validation

The bundled helper does not import Imagen-Pytorch and never trains or generates. From the `video-and-inpainting` sub-skill directory, use it to catch common failures before allocating a model.

```bash
# Text-to-video shape plan.
python scripts/video_shape_quickcheck.py \
  --operation sample \
  --video-model \
  --video-frames 20 \
  --temporal-downsample-factor 2,1 \
  --texts 4

# Video inpainting with per-frame masks.
python scripts/video_shape_quickcheck.py \
  --operation inpaint-video \
  --video-model \
  --video-shape 4,3,8,512,512 \
  --mask-shape 4,8,512,512 \
  --temporal-downsample-factor 2,1 \
  --texts 4

# Image-only pretraining through a Unet3D video model.
python scripts/video_shape_quickcheck.py \
  --operation train \
  --video-model \
  --image-shape 4,3,64,64 \
  --texts 4
```
