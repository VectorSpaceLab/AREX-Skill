# Video and Inpainting Troubleshooting

Use this table to diagnose failures before running expensive generation or training.

## Shape and argument assertions

| Symptom or message | Likely cause | Fix |
| --- | --- | --- |
| `video_frames must be passed in on sample time if training on video` | The model contains a `Unet3D` and `sample()` was called without `video_frames` or `inpaint_videos`. | Pass `video_frames=F`, or pass `inpaint_videos` whose shape supplies `F`. |
| `input to 3d unet must have 5 dimensions` | Direct `Unet3D.forward` received an image tensor or wrong video layout. | Use `(batch, channels, frames, height, width)`. For parent/trainer training, 4D image input is accepted and converted to one frame. |
| Output or mask has unexpected frame axis | Tensor order was supplied as `(batch, frames, channels, height, width)` or another layout. | Reorder to `(batch, channels, frames, height, width)` before model calls. Masks use `(batch, frames, height, width)` only because they have no channel axis. |
| `inpaint images and masks must be both passed in to do inpainting` | Only one of `inpaint_images`/`inpaint_videos` or `inpaint_masks` was provided. | Always pass the image/video tensor and mask together. |
| Inpainting batch assertion | Inpaint batch does not match `batch_size` or text batch. | Match `inpaint_* .shape[0]` to number of prompts. For unconditional sampling, set `batch_size` explicitly unless relying on the single-batch broadcast behavior. |
| Video mask frame assertion | Per-frame mask shape `(batch, frames, height, width)` has a different frame count from `inpaint_videos.shape[2]`. | Use the same frame count or pass a shared mask `(batch, height, width)` to broadcast across frames. |
| `downsample factor of last stage must be 1` | Last `temporal_downsample_factor` is not 1. | End the tuple with `1`, for example `(4, 2, 1)` or `(2, 1)`. |
| `temporal downsample factor must be in order of descending` | Factors are not sorted high-to-low. | Use descending order matching cascade progression, e.g. `(4, 2, 1)`, not `(1, 2, 4)`. |
| `number of input frames ... must be divisible by ...` | Video frame count is not divisible by `Unet3D.total_temporal_divisor` or by a temporal downsample factor. | Pick frame counts divisible by all relevant temporal divisors, or set `ignore_time=True` only for deliberate still-image/temporal-ablation training. |
| `trying to temporally downsample a conditioning video frames ... not neatly divisible` | `cond_video_frames` or `post_cond_video_frames` length is not divisible by the stage's downsample scale. | Use conditioning-frame lengths divisible by each stage factor, or set `resize_cond_video_frames=False` and provide already-correct per-stage shapes. |
| `conditioning images must have 4 dimensions only... use cond_video_frames instead` | `cond_images` was used with a 5D video prompt. | Use `cond_video_frames` or `post_cond_video_frames` for frame prompts; keep `cond_images` 4D. |
| `one cannot sample from null / placeholder unets` or `cannot sample from null unet` | Cascade includes `NullUnet` at a stage that `sample()` is trying to execute. | Do not use `NullUnet` in normal video cascades. For placeholder image cascades, choose start/stop stages so sampling does not execute the null stage. |
| `converting sampled video tensor to video file is not supported yet` | `return_pil_images=True` was requested on a video model. | Use `return_pil_images=False`; save returned 5D tensor with a separate video/image-grid utility. |

## Expensive runtime issues

| Symptom | Likely cause | Practical response |
| --- | --- | --- |
| CUDA out of memory during video sampling | 5D tensors multiply memory by frame count and every cascade stage may keep large activations. | Reduce `video_frames`, batch size, `image_sizes`, `dim`, number of stages, or sampling steps. Keep `use_one_unet_in_gpu=True` for cascades. |
| Sampling is very slow | Video diffusion repeats denoising steps over frames and stages. | Use tiny shapes only for wiring checks; realistic quality requires practical CUDA-scale time and memory. |
| Poor quality or no motion | Construction did not verify quality; model is untrained or undertrained. | Treat examples as API wiring. Train/fine-tune with sufficient data and compute before evaluating quality. |
| Conditioning frames appear ignored | Frame lengths may be downsampled, wrong order, or incompatible with temporal divisors. | Preflight `cond_video_frames`/`post_cond_video_frames`; confirm `resize_cond_video_frames` behavior and use 5D layout. |
| Image-only pretraining unexpectedly ignores time | This is intentional for 4D inputs to a video model. | Use 5D video batches and `ignore_time=False` when temporal learning is intended. Also preflight one-frame compatibility with `temporal_downsample_factor`; factors greater than 1 can still fail during frame-dimension derivation. |

## Quick preflight commands

From the `video-and-inpainting` sub-skill directory:

```bash
python scripts/video_shape_quickcheck.py \
  --operation sample --video-model --video-frames 16 --temporal-downsample-factor 4,2,1

python scripts/video_shape_quickcheck.py \
  --operation inpaint-video --video-model --video-shape 2,3,8,64,64 --mask-shape 2,8,64,64 --texts 2

python scripts/video_shape_quickcheck.py \
  --operation train --video-model --image-shape 2,3,64,64 --texts 2
```
