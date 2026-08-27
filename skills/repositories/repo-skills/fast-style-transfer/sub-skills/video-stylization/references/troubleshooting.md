# Video Stylization Troubleshooting

## Missing checkpoint or input video

The wrapper may proceed into `evaluate.ffwd_video` without running its own `check_opts`, so missing paths can surface as lower-level TensorFlow/moviepy errors. Run the bundled validator first:

```bash
python sub-skills/video-stylization/scripts/validate_video_stylization_inputs.py --checkpoint checkpoints/udnie --in-path input.mp4 --out-path out.mp4 --check-dependencies
```

## Moviepy import errors

**Symptoms**: `ModuleNotFoundError: No module named 'moviepy'` or import failures for `moviepy.video.io...`.

Install moviepy in the same Python environment used to run the bundled video stylization runtime, then re-run the validator with `--check-dependencies`.

## ffmpeg or codec errors

**Symptoms**: writer initialization fails, codec not found, output file cannot be opened, or container/audio errors.

Likely causes:

- ffmpeg executable or imageio-ffmpeg binary is unavailable.
- The requested output container/codec is unsupported.
- Input audio/container metadata interacts poorly with moviepy's writer.

Recovery:

- Run the validator with `--check-dependencies` and `--probe-video`.
- Try a simple `.mp4` output path first.
- Test a short clip before long videos.
- If audio is not required, consider stripping audio in a separate approved ffmpeg step before stylization.

## CPU video processing is too slow

Video stylization processes every frame. CPU mode can be useful for a tiny test but is slow for real footage. Verify TensorFlow GPU support and use `--device /gpu:0` when possible.

## Out-of-memory errors

Frame tensors have shape `(batch_size, height, width, 3)`. High-resolution videos and large batches can exceed memory. Lower `--batch-size`, test on a short clip, or downscale the video in a separate preprocessing step.

## Checkpoint restore errors

A video run uses the same transform-network checkpoint restore as image stylization. Restore failures usually mean missing files, wrong checkpoint path, incompatible graph, or TensorFlow version drift. First verify image stylization on one frame or still image before debugging moviepy.

## `--tmp-dir` or `--no-disk` does not behave as expected

The bundled video runtime parses these options but its main path calls `evaluate.ffwd_video` directly. Do not rely on temporary frame directories or no-disk toggles unless a refreshed skill proves different behavior.

## Output file exists but looks wrong

Confirm that:

- The checkpoint is for the intended style.
- The input video was read with expected color/dimensions.
- The output file has the same approximate duration/FPS.
- The batch size did not trigger memory/resource failures.
- A still-image run with the same checkpoint produces plausible output.
