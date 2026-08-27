# Generation troubleshooting

Use this page for failures that happen while creating frames, videos, or audio
weight curves.

## Prompt / seed / size validation

### `ValueError` about prompt or seed counts

- For `walk(...)`, the number of seeds must match the number of prompts.
- For `generate_images(...)`, the number of seeds must equal
  `batch_size * num_batches`.

Fix the input counts first. Do not retry the generation until the counts match.

### `height` / `width` divisible-by-8 errors

The walk pipeline requires both dimensions to be divisible by 8. Pick values
such as 512, 576, 640, and so on.

### Interpolation-step length mismatch

If `num_interpolation_steps` is a list, it must have one entry per prompt gap.
If you are using audio pacing, make sure the derived timing array has the length
expected by the number of frames.

## Audio interpolation problems

### Missing or wrong audio file

`get_timesteps_arr(...)` needs a real audio file path. Check that the file exists
and that the offset/duration window fits inside the source clip.

### Unexpected interpolation curve

If the resulting curve is too spiky or too linear, adjust:

- `margin` to change the harmonic/percussive separation behavior
- `smooth` to blend toward a linear ramp
- `fps` to increase or reduce the number of output weights

Use `scripts/preview_audio_timesteps.py` to inspect the curve before a long run.

## Upsampling failures

### `ImportError` or build failure from `realesrgan` / `basicsr`

The upsampler stack is optional and heavier than the core walk workflow. If the
build fails, confirm that the active environment already has a working torch
stack and then reinstall the optional upsampling dependencies. If you do not
need upsampling, skip it.

### CPU upsampling is too slow

That path is technically available but usually impractical. Prefer CUDA when you
intend to use `upsample=True`.

## Video encoding failures

### `make_video_pyav(...)` or `write_video(...)` errors

Check these prerequisites in order:

1. `av` imports cleanly.
2. `ffmpeg` is on `PATH`.
3. `ffmpeg -encoders` lists `libx264`.
4. The output directory is writable.

If the error mentions `write_video` but the package import still works, the
Python `av` wheel or the system ffmpeg stack is usually the problem.

## Memory and backend issues

### CUDA out-of-memory

Lower one of these first:

- `height` / `width`
- `batch_size`
- `num_inference_steps`
- `upsample`

### MPS note

The README recommends `torch.float32` on Apple MPS. Do not assume `float16`
will behave the same way as on CUDA.

## Output / resume problems

### `resume=True` fails

Confirm that the named output directory already exists and contains a
`prompt_config.json` from a previous run.

### Missing frames or partial clips

If a previous run was interrupted, inspect the named output directory before
restarting. The pipeline can resume from partially written frames when the saved
metadata is intact.
