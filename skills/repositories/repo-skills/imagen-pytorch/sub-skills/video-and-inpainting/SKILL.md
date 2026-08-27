---
name: video-and-inpainting
description: "Use Imagen-Pytorch video generation and image/video inpainting
  APIs, including Unet3D tensor shapes, sampling frame counts, conditioning
  frames, masks, and safe preflight validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# video-and-inpainting

Use this sub-skill when the task mentions `Unet3D`, text-to-video, `video_frames`, `temporal_downsample_factor`, `cond_video_frames`, `post_cond_video_frames`, `inpaint_images`, `inpaint_videos`, `inpaint_masks`, `ignore_time`, or video limitations around `return_pil_images`.

## Route first

- Generic text-to-image, super-resolution image sampling, or PIL image return: use [image-generation](../image-generation/SKILL.md).
- Training loops, EMA, checkpoint save/load, or trainer internals: use [training-and-checkpointing](../training-and-checkpointing/SKILL.md).
- Dataset folders, Hugging Face datasets, captions, T5 text encodings, and data collation: use [data-and-text-conditioning](../data-and-text-conditioning/SKILL.md).
- Stay here for video-specific Imagen/ElucidatedImagen setup, conditioning frames, and image/video inpainting arguments.

## Non-negotiable shape contract

- Video tensors are always `(batch, channels, frames, height, width)`.
- Image tensors are `(batch, channels, height, width)`.
- Inpainting masks are boolean-like `(batch, height, width)` for images; for videos they may be `(batch, height, width)` to broadcast across frames or `(batch, frames, height, width)` for per-frame masks.
- Imagen and ElucidatedImagen become video models if any cascade stage is a `Unet3D`; video sampling then needs `video_frames` unless it is inferred from `inpaint_videos`.
- `temporal_downsample_factor` is per cascade stage, must be descending, and the last stage must be `1`.
- Video/PIL conversion is not implemented; use `return_pil_images=False` for video samples and save the returned tensor with your own video writer.

## Safe workflow

1. Choose `Unet3D` stages for video. Use only `Unet3D` stages for ordinary video cascades; do not sample through a `NullUnet` placeholder.
2. Choose frame counts before model calls. For a cascade with `temporal_downsample_factor=(2, 1)` and `video_frames=20`, the base stage sees 10 frames and the final stage sees 20.
3. From this sub-skill directory, run the bundled preflight checker before expensive model calls:

   ```bash
   python scripts/video_shape_quickcheck.py \
     --operation sample \
     --video-model \
     --video-frames 20 \
     --temporal-downsample-factor 2,1 \
     --texts 4
   ```

4. Keep generation and training on practical CUDA-scale hardware. Construction only established a CUDA torch smoke; it did not prove realistic video quality or affordable full generation.
5. For API details and copyable recipes, use [workflows](references/workflows.md), [api-reference](references/api-reference.md), and [troubleshooting](references/troubleshooting.md).

## Minimal decision rules

- Text-to-video sampling: call `sample(..., texts=[...], video_frames=F, return_pil_images=False)`.
- Video inpainting: call `sample(..., inpaint_videos=videos, inpaint_masks=masks, return_pil_images=False)`; `videos` supplies `F`.
- Image inpainting: call `sample(..., inpaint_images=images, inpaint_masks=masks)` and keep image shapes 4D.
- Image-only pretraining with `Unet3D`: pass images as 4D; the model path converts them to single-frame videos and sets `ignore_time=True` automatically. Preflight temporal factors first, because the source still derives one-frame cascade dimensions before temporal modules are skipped.
- Conditioning with preceding/following frames: pass 5D `cond_video_frames` and/or `post_cond_video_frames`; keep frame lengths divisible after temporal downsampling.
