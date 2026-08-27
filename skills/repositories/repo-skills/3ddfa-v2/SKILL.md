---
name: "3ddfa-v2"
description: "Routes 3DDFA_V2 face-alignment setup, still-image demos, video
  tracking, and ONNX benchmarking workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# 3DDFA_V2

Use this skill for the 3DDFA_V2 face-alignment repo. The public workflow is a
small pipeline: build the native pieces, then run still-image, video/tracking,
or ONNX/benchmark commands.

## Start here

1. If anything fails to build or import, open `references/troubleshooting.md`.
2. If you need model files or config choices, open `references/model-assets.md`.
3. If you need class/function details, open `references/api-reference.md`.
4. Run the setup route first whenever `render.so`, `cpu_nms`, or `Sim3DR_Cython`
is missing.

The repository is source-first, not a packaged wheel. Use the bundled helpers in
this skill tree instead of calling the original repo scripts directly.

## Routes

### `setup-and-assets`
Use when the user asks to install or verify the runtime, build compiled pieces,
check checkpoint/config assets, or fix import/build failures.

Read `sub-skills/setup-and-assets/SKILL.md`, `references/model-assets.md`, and
`references/troubleshooting.md`.

Use the bundled helpers:
- `scripts/build_native_extensions.py`
- `scripts/check_assets.py`
- `scripts/check_core_imports.py`

### `still-image-demo`
Use for single-image inference, 2D landmark overlays, 3D renderings, depth,
PNCC, UV texture, pose boxes, PLY, or OBJ exports.

Read `sub-skills/still-image-demo/SKILL.md` and
`sub-skills/still-image-demo/references/workflows.md`.

Use `sub-skills/still-image-demo/scripts/run-still-image.py` for a headless-friendly wrapper.

### `video-and-tracking`
Use for MP4/AVI processing, tracking, smoothing, or frame-window control.

Read `sub-skills/video-and-tracking/SKILL.md` and
`sub-skills/video-and-tracking/references/workflows.md`.

Use `sub-skills/video-and-tracking/scripts/run-video.py` and `sub-skills/video-and-tracking/scripts/run-video-smooth.py`.

### `onnx-and-benchmarking`
Use for ONNX acceleration, CPU latency, thread tuning, or microbenchmarks.

Read `sub-skills/onnx-and-benchmarking/SKILL.md` and
`sub-skills/onnx-and-benchmarking/references/workflows.md`.

Use `sub-skills/onnx-and-benchmarking/scripts/run-latency.py` and `sub-skills/onnx-and-benchmarking/scripts/run-speed-cpu.py`.

## Common runtime facts

- Default config: `configs/mb1_120x120.yml`.
- Alternate configs: `configs/mb05_120x120.yml` and `configs/resnet_120x120.yml`.
- Provide an input image or video path for demos; local smoke fixtures may be used when the checkout includes them.
- Generated outputs live under `examples/results/`.
- `demo.py` supports `2d_sparse`, `2d_dense`, `3d`, `depth`, `pncc`, `uv_tex`,
  `pose`, `ply`, and `obj`.
- `demo_video.py` and `demo_video_smooth.py` support `2d_sparse` and `3d`;
  webcam mode is manual-only and is documented, but not bundled as a runnable helper.
- `--onnx` switches the demo pipeline to the CPU-friendly ONNX path.
- `uv_tex` needs SciPy and the BFM UV/config assets.
- The repo still references deprecated NumPy aliases such as `np.long`, so the
  bundled runtime helpers restore a compatibility layer before importing the
  pipeline.

## Headless use

The bundled helpers default to headless plotting behavior so they work in
non-GUI environments. If you need interactive windows, override that behavior
explicitly.

## What not to route here

- Experimental Gradio notebook/demo code.
- Generic face detection tasks that do not involve the 3DDFA_V2 alignment
  pipeline.
- Training or dataset creation tasks; this repo is inference-oriented.
