---
name: video-stylization
description: "Guides Fast Style Transfer transform_video.py and ffwd_video
  checkpoint-based video stylization, moviepy/ffmpeg checks, device/batch
  choices, and video troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: CC BY-NC 4.0
---

# Video Stylization

Use this sub-skill when the user has a trained Fast Style Transfer checkpoint and wants to apply it to a video, or when they need to debug moviepy, ffmpeg, video input/output, checkpoint restore, device, batch-size, or performance problems.

## Read and run

- Read [references/video-stylization-workflow.md](references/video-stylization-workflow.md) for command recipes, prerequisites, checkpoint handoff, frame batching behavior, CPU/GPU caveats, and output validation.
- Read [references/cli-reference.md](references/cli-reference.md) for verified the bundled video stylization runtime flags and `evaluate.ffwd_video` behavior.
- Read [references/troubleshooting.md](references/troubleshooting.md) for checkpoint, moviepy, ffmpeg, codec/audio, output path, memory, and backend failures.
- Run [scripts/validate_video_stylization_inputs.py](scripts/validate_video_stylization_inputs.py) before processing frames. It checks paths, dependency availability, optional video metadata, and option semantics without restoring checkpoints or writing video.

## When to use this route

Use this route for requests like:

- "Stylize an MP4 with a Fast Style Transfer checkpoint."
- "Check whether moviepy/ffmpeg are ready before running the bundled video stylization runtime."
- "Run video stylization on CPU because TensorFlow GPU is unavailable."
- "Why did video encoding or audio handling fail?"
- "How should I choose `--batch-size` for frames?"

Route away when:

- The user needs to create a checkpoint first: [../training/SKILL.md](../training/SKILL.md)
- The user needs still-image or image-directory stylization: [../image-stylization/SKILL.md](../image-stylization/SKILL.md)

## Command pattern

```bash
python sub-skills/video-stylization/scripts/run_video_stylization.py \
  --checkpoint checkpoints/udnie \
  --in-path content/input.mp4 \
  --out-path outputs/input_udnie.mp4 \
  --device /gpu:0 \
  --batch-size 4
```

CPU debug pattern:

```bash
python sub-skills/video-stylization/scripts/run_video_stylization.py \
  --checkpoint checkpoints/udnie \
  --in-path content/input.mp4 \
  --out-path outputs/input_udnie.mp4 \
  --device /cpu:0 \
  --batch-size 1
```

Preflight:

```bash
python sub-skills/video-stylization/scripts/validate_video_stylization_inputs.py \
  --checkpoint checkpoints/udnie \
  --in-path content/input.mp4 \
  --out-path outputs/input_udnie.mp4 \
  --device /cpu:0 \
  --batch-size 1 \
  --check-dependencies \
  --probe-video
```

## Behavior facts

- the bundled video stylization runtime is a thin wrapper around `evaluate.ffwd_video`.
- `evaluate.ffwd_video` opens the input through moviepy, creates an ffmpeg writer, batches frames, runs the transform network, clips predictions to `uint8`, and writes output frames.
- The repository implementation opens the input video with `audio=False` while the ffmpeg writer passes `audiofile=path_in`; audio/container behavior can therefore depend on moviepy/ffmpeg compatibility.
- Default CLI device is `/gpu:0`; CPU works for small debugging but is usually slow for real videos.
- The parsed `--tmp-dir` and `--no-disk` options are documented parser surfaces, but the inspected `main()` calls `evaluate.ffwd_video` directly and does not use them for a disk-frame workflow.

## Validation limits

The bundled validator can check path existence, dependency imports, optional video metadata, output parent directory, device string, and batch-size sanity. It cannot prove checkpoint compatibility, frame-by-frame TensorFlow inference, codec support for every output container, or acceptable runtime performance.
