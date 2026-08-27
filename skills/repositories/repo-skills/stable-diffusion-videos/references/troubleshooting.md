# Troubleshooting

This page covers issues shared by the whole package. For workflow-specific
recovery steps, see the matching sub-skill troubleshooting file.

## Import and install problems

### `CLIPFeatureExtractor`, `AutoImageProcessor`, `Dinov2WithRegistersConfig`, or `_pytree.register_pytree_node` import errors

These usually mean the `torch` / `torchvision` / `transformers` / `diffusers`
set is out of sync. Reinstall a matched quartet instead of upgrading one package
at a time.

Signals seen in practice:

- `ImportError: cannot import name 'CLIPFeatureExtractor'`
- `ImportError: cannot import name 'Dinov2WithRegistersConfig'`
- `ModuleNotFoundError: Could not import module 'AutoImageProcessor'`
- `AttributeError: module 'torch.utils._pytree' has no attribute 'register_pytree_node'`

### `torchvision::nms` or `torchvision.io` failures

If `torchvision` fails on import or `write_video` is missing, the wheel pair is
usually incompatible or the build is incomplete. Reinstall `torch` and
`torchvision` together as a matched CUDA pair, then rerun the smoke check.

### NumPy 2 warnings with compiled wheels

If you see messages such as:

- `A module that was compiled using NumPy 1.x cannot be run in NumPy 2.x`
- `Failed to initialize NumPy: _ARRAY_API not found`

switch to a NumPy 1.x build that matches the compiled wheels, or rebuild the
packages that depend on NumPy. The video stack is sensitive to this mismatch.

### `realesrgan` / `basicsr` build isolation failures

If `basicsr` tries to build in isolation and reports that `torch` is missing,
install the torch stack first in the active environment and then reinstall the
upsampling extras. The upsampler is optional, so you can also skip it when it is
not needed.

## Generation/runtime problems

### `height` and `width` validation

Both values must be divisible by 8. The walk pipeline raises a `ValueError` if
that constraint is violated.

### Prompt and seed counts

The number of seeds must match the number of prompts for `walk(...)` and must
match `batch_size * num_batches` for `generate_images(...)`.

### Interpolation-step length

If `num_interpolation_steps` is a list, it must have one entry per prompt gap.
If `audio_filepath` is used, the computed timing array must also have the
expected length.

### Resume mode

`resume=True` expects a named output directory with an existing
`prompt_config.json`. If the metadata is missing, start a fresh run instead of
trying to resume.

### Video encoding failures

If `make_video_pyav(...)` or `torchvision.io.write_video(...)` fails, check:

- `av` imports cleanly in the active environment.
- `ffmpeg` is on `PATH`.
- `ffmpeg -encoders` lists `libx264`.

### GPU memory pressure

The walk pipeline is GPU-oriented and can exhaust VRAM quickly at larger image
sizes, batch sizes, or inference-step counts. Reduce one of those dimensions
first.

### MPS note

On Apple MPS, the README recommends `torch.float32` rather than `torch.float16`.

## Self-check helper

Use `scripts/check_env.py` to catch import, backend, and tiny video/audio smoke
failures before you attempt a full generation run.
