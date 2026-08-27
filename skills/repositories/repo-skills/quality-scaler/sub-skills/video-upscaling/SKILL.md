---
name: video-upscaling
description: "Guides QualityScaler video frame extraction, resume, encoding,
  codec fallback, and cleanup."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# video-upscaling

Use this sub-skill when the task is about upscaling videos, extracting frames, resuming a partially completed job, choosing codecs, or troubleshooting frame/encode behavior.

## Read this when

- The user wants to upscale a video rather than a still image.
- The task mentions frame extraction, resume, or keep-frames behavior.
- You need to explain how the output folder or output filename is formed for videos.
- Encoding fails and codec fallback matters.
- The job appears to stall, stop, or resume unexpectedly.

## What this sub-skill owns

- `VideoUpscaleTask` and the video job lifecycle.
- Frame extraction, frame naming, and resume detection.
- Multiprocess frame upscaling and the save queue/thread.
- Encoding, codec selection, and libx264 fallback.
- Keep-frames cleanup and metadata copy after encode.

## What belongs elsewhere

- Launch, provider, model, and asset readiness belong in `setup-runtime`.
- Still-image AI details belong in `image-upscaling`.
- Shared suffix rules and supported extensions live in the root references.

## Core workflow

1. Read `references/video-task-lifecycle.md` for the end-to-end job sequence.
2. Read `references/frame-resume-and-encode-matrix.md` for codec mapping and resume rules.
3. Read `references/video-failure-modes.md` for frame-extraction, encoding, and stop/resume failures.
4. Use `../../scripts/derive_qualityscaler_paths.py` to preview video and frame output names.

## Important facts

- Video jobs build a task object before extraction begins.
- Frame extraction uses `ffmpeg.exe` and writes a `frame_###.jpg` sequence.
- Resume detection is filename-based: the app looks for already upscaled frames in the target folder.
- The image AI core from `image-upscaling` is reused for each frame.
- Encoding first tries the selected codec and then falls back to `libx264`.

## Common user intents

- "Why did the video restart from scratch?" -> check the resume matrix.
- "Why did encoding fail?" -> check the codec fallback and the ffmpeg asset.
- "Why is there a frame folder left behind?" -> inspect the keep-frames setting and cleanup step.
- "What output will this video create?" -> run the path helper script.

## Bundled references

- `references/video-task-lifecycle.md`
- `references/frame-resume-and-encode-matrix.md`
- `references/video-failure-modes.md`

## Bundled scripts

- `../../scripts/derive_qualityscaler_paths.py` for output-name previews.

## Stop conditions

If the video job fails because the runtime, model file, or provider is missing, route back to `setup-runtime` before debugging the pipeline.
