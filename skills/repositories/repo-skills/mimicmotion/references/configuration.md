# Configuration and assets

## Purpose

Read this before running the model so the input files, checkpoint files, and config values match what MimicMotion expects.

## Canonical sample config

The repository ships `configs/test.yaml` as the reference local-inference config.

```yaml
base_model_path: stabilityai/stable-video-diffusion-img2vid-xt-1-1
ckpt_path: models/MimicMotion_1-1.pth
test_case:
  - ref_video_path: assets/example_data/videos/pose1.mp4
    ref_image_path: assets/example_data/images/demo1.jpg
    num_frames: 72
    resolution: 576
    frames_overlap: 6
    num_inference_steps: 25
    noise_aug_strength: 0
    guidance_scale: 2.0
    sample_stride: 2
    fps: 15
    seed: 42
```

## What the fields mean

- `base_model_path`: the Stable Video Diffusion base model ID or local path used by `create_pipeline`.
- `ckpt_path`: the MimicMotion checkpoint file. The v1-1 checkpoint is the default runtime target.
- `test_case`: one or more inference jobs. The CLI loops over these entries and produces one MP4 per item.

## Inference and predictor inputs

### Reference image / motion video
- `ref_image_path` or `appearance_image`: the starting frame used for appearance guidance.
- `ref_video_path` or `motion_video`: the motion source from which DWPose keypoints are extracted.

### Size and layout controls
- `resolution`: the main size scalar.
- The repo's preprocessing resizes and center-crops to a 9:16-like target derived from this scalar, then snaps the result to 64-pixel multiples.
- `resolution` must be a multiple of 8 in the Cog predictor and must stay within 64-1024.

### Generation controls
- `num_frames` / `chunk_size`: the number of frames to generate per tile.
- `frames_overlap`: overlapping frames between tiles for smoother transitions.
- `num_inference_steps` / `denoising_steps`: diffusion steps.
- `noise_aug_strength` / `noise_strength`: noise strength used for conditioning.
- `guidance_scale`: classifier-free guidance strength.
- `sample_stride`: frame sampling interval for the reference video.
- `fps` / `output_frames_per_second`: output playback rate.
- `seed`: integer seed; the Cog path randomizes it when omitted.

## Required asset layout

```text
models/
  DWPose/
    yolox_l.onnx
    dw-ll_ucoco_384.onnx
  MimicMotion_1-1.pth
  MimicMotion.pth            # legacy option used by checkpoint_version='v1'
```

The Stable Video Diffusion base weights are fetched automatically by the pipeline and may live in the Hugging Face cache or under the same `models/` tree depending on how the environment is prepared.

## Practical defaults to remember

- `checkpoint_version='v1-1'` is the default Cog setting.
- `chunk_size=16` and `frames_overlap=6` are the default Cog settings.
- `num_frames=72`, `resolution=576`, `guidance_scale=2.0`, `fps=15`, and `seed=42` are the sample config defaults.
- `sample_stride=2` is the sample config default.
