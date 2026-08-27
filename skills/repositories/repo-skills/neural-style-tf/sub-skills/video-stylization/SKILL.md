---
name: video-stylization
description: "Plan neural-style-tf video and frame-sequence stylization with
  frame extraction, optical flow, temporal consistency, and safe command
  assembly."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# video-stylization

Use this sub-skill when the user wants neural-style transfer over a video or numbered frame sequence, especially when temporal consistency, optical-flow files, frame initialization, or video reassembly are involved.

Do not use this sub-skill for:

- one-off still-image runs; use [image-stylization](../image-stylization/SKILL.md).
- style interpolation, masks, original colors, layer weights, or optimizer tuning that applies equally to still images; use [advanced-controls](../advanced-controls/SKILL.md).
- dependency installation, TensorFlow 1.x compatibility, VGG weights, or cross-cutting runtime checks; use [root runtime notes](../../references/runtime-and-installation.md) and [root troubleshooting](../../references/troubleshooting.md).

## Operating route

1. Confirm the runtime is suitable: video is expensive, the repo wrapper refuses non-GPU runs, and full execution requires VGG-19 weights plus a TensorFlow 1.x-compatible runtime.
2. Read [references/video-workflow.md](references/video-workflow.md) to choose either an end-to-end video plan or a pre-extracted frame-sequence plan.
3. Read [references/optical-flow-files.md](references/optical-flow-files.md) before using `--init_frame_type prev_warped`, because the source expects specific `.flo` and `reliable_*.txt` filenames.
4. Use [scripts/plan_video_pipeline.py](scripts/plan_video_pipeline.py) to print a non-destructive command plan. It does not delete frames, download models, run optical flow, or render unless a future operator intentionally replaces the printed placeholders.
5. If a video command fails, check [references/troubleshooting.md](references/troubleshooting.md) for ffmpeg/ffprobe, GPU, flow-file, frame-format, and cleanup-related failures.

## Minimum inputs for a full video run

- A video file or pre-extracted frame directory.
- One or more style images, normally handled by the still-image and advanced-control routes.
- VGG-19 MatConvNet weights reachable by `neural_style.py`.
- `ffmpeg` and `ffprobe` or equivalent frame extraction/assembly tools when starting from a video file.
- Optical-flow and consistency files if using `--init_frame_type prev_warped` or source-compatible temporal consistency.
- A compatible GPU runtime for feasible full video rendering. CPU-only video plans are useful for command review but are not practical for long videos.

Full end-to-end video execution was not selected as a required verification target for this generated skill because it is GPU-, model-weight-, and time-dependent. The verified scope covers source/static behavior and safe command planning.
