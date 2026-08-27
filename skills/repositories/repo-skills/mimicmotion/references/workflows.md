# Workflows

## Purpose

Read this when you want the exact step sequence for MimicMotion's two supported user-facing workflows: local inference from a checkout and Cog-based deployment.

## 1) Local inference from a checkout

Use this path when you have a MimicMotion checkout, the model weights are present, and you want to generate a video from the sample config or a custom config.

### Sequence

1. Prepare the CUDA environment described in `references/environment.md`.
2. Place the required local weights under `models/`.
3. Preflight the runtime:

```bash
python scripts/check_runtime.py --repo-root /path/to/MimicMotion
```

4. Run the wrapped inference entry point:

```bash
python scripts/run_inference.py \
  --repo-root /path/to/MimicMotion \
  --inference-config configs/test.yaml \
  --output-dir outputs/
```

### What happens

- The repository config is read from `configs/test.yaml` unless you pass another file.
- Each `test_case` entry produces one MP4.
- The source code uses `assets/example_data/videos/pose1.mp4` and `assets/example_data/images/demo1.jpg` in the sample config.
- The output filename is derived from the reference-video basename and a timestamp.

### When this path fails

- Missing model files: check `references/configuration.md` and `references/troubleshooting.md`.
- Missing CUDA: do not switch to CPU; the skill treats CUDA as required.
- `ffmpeg` missing: install it in the same environment or system prefix.

## 2) Cog deployment / predictor workflow

Use this path when you want the repository's deployment surface, validation rules, and weight-fetch behavior.

### What the predictor does

- `Predictor.setup` downloads `DWPose.tar`, `MimicMotion.pth`, `MimicMotion_1-1.pth`, and `SVD.tar` into `models/` using `pget`.
- `Predictor.predict` accepts a motion video and appearance image, validates the numeric bounds, optionally switches between `v1` and `v1-1`, and writes a temporary MP4.
- The predictor is GPU-oriented and expects the same core CUDA stack as local inference.

### Important inputs

- `motion_video`
- `appearance_image`
- `resolution`
- `chunk_size`
- `frames_overlap`
- `denoising_steps`
- `noise_strength`
- `guidance_scale`
- `sample_stride`
- `output_frames_per_second`
- `seed`
- `checkpoint_version` (`v1` or `v1-1`, default `v1-1`)

### Validation rules worth remembering

- `resolution` must be divisible by 8 and stay in the range 64-1024.
- `chunk_size` must be at least 2 and greater than `frames_overlap`.
- `denoising_steps` must stay in 1-100.
- `noise_strength` must stay in 0.0-1.0.
- `guidance_scale` must stay in 0.1-10.0.
- `sample_stride` must be at least 1.
- `output_frames_per_second` must stay in 1-60.

## Choosing between the two

- Choose local inference for direct generation in a checkout.
- Choose Cog when you are validating deployment packaging or a hosted predictor surface.
- Both workflows share the same model stack, the same weight layout, and the same CUDA requirement.
