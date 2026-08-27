# Video Stylization Workflow

## Purpose

This reference explains how to apply a trained Fast Style Transfer checkpoint to a video using the bundled video stylization runtime and the underlying `evaluate.ffwd_video` function.

## Required inputs

| Input | Flag | Notes |
| --- | --- | --- |
| Trained checkpoint | `--checkpoint` | Directory or path/prefix restorable by TensorFlow Saver. |
| Input video | `--in-path` | Moviepy-readable video file. |
| Output video | `--out-path` | Destination file; parent directory should exist. |
| Device | `--device` | TensorFlow device string such as `/gpu:0` or `/cpu:0`. |
| Batch size | `--batch-size` | Number of frames processed per TensorFlow batch. |
| Dependencies | none as flags | moviepy and ffmpeg/imageio-ffmpeg must be available. |

## Recommended preflight

```bash
python sub-skills/video-stylization/scripts/validate_video_stylization_inputs.py \
  --checkpoint checkpoints/udnie \
  --in-path videos/input.mp4 \
  --out-path outputs/input_udnie.mp4 \
  --device /gpu:0 \
  --batch-size 4 \
  --check-dependencies \
  --probe-video
```

Use `--probe-video` only when it is safe to open the file for metadata. It does not write frames.

## Launch pattern

```bash
mkdir -p outputs
python sub-skills/video-stylization/scripts/run_video_stylization.py \
  --checkpoint checkpoints/udnie \
  --in-path videos/input.mp4 \
  --out-path outputs/input_udnie.mp4 \
  --device /gpu:0 \
  --batch-size 4
```

If TensorFlow GPU is unavailable, use a small CPU debug run first:

```bash
python sub-skills/video-stylization/scripts/run_video_stylization.py --checkpoint checkpoints/udnie --in-path videos/short.mp4 --out-path outputs/short_udnie.mp4 --device /cpu:0 --batch-size 1
```

## Underlying frame flow

`evaluate.ffwd_video(path_in, path_out, checkpoint_dir, device_t='/gpu:0', batch_size=4)` performs the main work:

1. Opens the input with `VideoFileClip(path_in, audio=False)`.
2. Opens an `FFMPEG_VideoWriter` with the input size and FPS.
3. Builds the transform network graph for batches shaped `(batch_size, height, width, 3)`.
4. Restores the checkpoint.
5. Iterates frames from the input clip.
6. Fills the last partial batch by repeating the last frame.
7. Runs TensorFlow predictions and writes clipped `uint8` output frames.
8. Closes the writer.

## Device and memory guidance

- Use `/gpu:0` when TensorFlow GPU is verified; video frame batches are computationally heavy.
- Use `/cpu:0` only for short tests or environments without GPU support.
- Lower `--batch-size` on memory errors or very high-resolution videos.
- Increase `--batch-size` only after a short representative clip succeeds.

## Output validation

After a run, check:

- The output file exists and has nonzero size.
- Moviepy or ffprobe can open it.
- Duration and FPS are close to the input.
- Visual output is stylized and not all-black/all-white.
- Audio behavior matches user expectations; if audio matters, test a short clip first.

## Limitations

- Video stylization requires a trained checkpoint; this workflow does not create one.
- The bundled video wrapper parses `--tmp-dir` and `--no-disk`, but the main path delegates directly to in-memory frame batching.
- ffmpeg availability and codec support vary by environment.
