# Inference and demo workflows

## Purpose

Use this file for the concrete command shapes, options, and output behavior of
BackgroundMattingV2 inference-time workflows.

## Model choice

- `mattingbase` returns coarse results only.
- `mattingrefine` returns full-resolution alpha and foreground plus coarse and
  refinement intermediates.
- `mobilenetv2` is the lightest backbone.
- `resnet50` and `resnet101` are heavier and typically used for stronger quality
  or training baselines.

## Output interpretation

The model API returns:

- `pha`: alpha matte
- `fgr`: foreground residual / foreground prediction
- `err`: coarse error estimate
- `hid`: hidden encoding for refinement
- `pha_sm`, `fgr_sm`, `err_sm`, `ref_sm`: refinement intermediates from
  `MattingRefine`

For compositing, the README formula is:

```text
com = pha * fgr + (1 - pha) * bgr
```

## Safe smoke-first workflow

```bash
python sub-skills/inference-and-demo/scripts/smoke_forward.py \
  --repo-root <repo-checkout> \
  --device cuda \
  --model-type mattingrefine \
  --backbone mobilenetv2 \
  --height 64 --width 64
```

Use `--backend torchscript` when you want to verify that scripting still works.
For the default `mattingrefine` / `mobilenetv2` / 64x64 smoke, expect six
output tensors: `pha`, `fgr`, `pha_sm`, `fgr_sm`, `err_sm`, and `ref_sm`, with
coarse outputs at 16x16 when `backbone_scale=0.25`.

## Image inference

Use the image wrapper in dry-run mode to inspect the exact command first:

```bash
python sub-skills/inference-and-demo/scripts/run_inference_images.py \
  --repo-root <repo-checkout> \
  --dry-run \
  -- \
  --model-type mattingrefine \
  --model-backbone mobilenetv2 \
  --model-checkpoint <checkpoint> \
  --images-src <src-dir> \
  --images-bgr <bgr-dir> \
  --output-dir <output-dir> \
  --output-types com pha fgr
```

Key points:

- `--preprocess-alignment` enables homographic alignment before matting.
- `ref` output requires `mattingrefine`.
- `err` output is available for `mattingbase` and `mattingrefine`.
- `com` output is a composited result directory.

## Video inference

Use the video wrapper in dry-run mode first:

```bash
python sub-skills/inference-and-demo/scripts/run_inference_video.py \
  --repo-root <repo-checkout> \
  --dry-run \
  -- \
  --model-type mattingrefine \
  --model-backbone mobilenetv2 \
  --model-checkpoint <checkpoint> \
  --video-src <src-video> \
  --video-bgr <background> \
  --output-dir <output-dir> \
  --output-types com pha fgr ref \
  --output-format video
```

Key points:

- `--video-target-bgr` composites onto a target background video.
- `--output-format video` writes MP4 files.
- `--output-format image_sequences` writes per-frame images.

## Webcam demo

The webcam demo is hardware and GUI gated. Read the source CLI help for exact
flags, then run it only when you have:

- a local camera
- a display / GUI session
- a CUDA-capable environment when you want practical responsiveness

Because this workflow is interactive, the bundled docs only describe it. They do
not auto-launch webcam capture.

## Throughput testing

The native `inference_speed_test.py` CLI is the best reference for throughput
claims. Use the smoke helper first, then use the native CLI only when you want
backend-specific timing on a real GPU or CPU path.

## Recommended settings

The README recommends:

- HD: `backbone_scale=0.25`, `refine_sample_pixels=80000`
- 4K: `backbone_scale=0.125`, `refine_sample_pixels=320000`

## Why this workflow fails

- the checkpoint path is wrong or missing
- source and background sizes do not match
- the chosen output type is incompatible with the model type
- CPU is too slow for live demos
- OpenCV cannot read the video or open the GUI window
- alignment fails because the frames do not have enough feature matches
