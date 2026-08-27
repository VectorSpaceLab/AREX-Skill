# API reference

This file lists the public package surface that the runtime skill relies on.
Use it when you need an exact signature, default, or output shape without
reopening the source checkout.

## Top-level exports

The package exports these names through `stable_diffusion_videos.__all__`:

- `StableDiffusionWalkPipeline`
- `FlaxStableDiffusionWalkPipeline`
- `generate_images`
- `generate_images_flax`
- `Interface`
- `RealESRGANModel`
- `get_timesteps_arr`
- `make_video_pyav`
- `upload_folder_chunked`

## Verified package version

- `stable_diffusion_videos.__version__ == 0.9.2`

## Core Torch pipeline

### `StableDiffusionWalkPipeline`

Constructor and `from_pretrained(...)` follow the Diffusers pipeline pattern.
The repo adds a `tiled` option to `from_pretrained(...)`.

#### `walk(...)`

```python
walk(
    prompts=None,
    seeds=None,
    num_interpolation_steps=5,
    output_dir="./dreams",
    name=None,
    image_file_ext=".png",
    fps=30,
    num_inference_steps=50,
    guidance_scale=7.5,
    eta=0.0,
    height=None,
    width=None,
    upsample=False,
    batch_size=1,
    resume=False,
    audio_filepath=None,
    audio_start_sec=None,
    margin=1.0,
    smooth=0.0,
    negative_prompt=None,
    make_video=True,
)
```

Returns the final video path when `make_video=True`. It creates a directory tree
under `output_dir/name/` with one clip directory per prompt pair.

Important constraints observed in the source:

- `prompts` and `seeds` must align.
- If `num_interpolation_steps` is an int, it is expanded to one value per gap
  between prompts.
- `height` and `width` must be divisible by 8.
- `audio_filepath` is optional; when present, the walk uses
  `get_timesteps_arr(...)` to steer interpolation.
- `resume=True` expects an existing `prompt_config.json` under the named run.
- `upsample=True` instantiates `RealESRGANModel` on demand.

#### Other helpful methods

- `embed_text(text, negative_prompt=None)`
- `init_noise(seed, noise_shape, dtype)`
- `make_clip_frames(...)`
- `enable_attention_slicing(...)`
- `disable_attention_slicing()`

## Still-image generation

### `generate_images(...)`

```python
generate_images(
    pipeline,
    prompt,
    batch_size=1,
    num_batches=1,
    seeds=None,
    num_inference_steps=50,
    guidance_scale=7.5,
    output_dir="./images",
    image_file_ext=".jpg",
    upsample=False,
    height=512,
    width=512,
    eta=0.0,
    push_to_hub=False,
    repo_id=None,
    private=False,
    create_pr=False,
    name=None,
)
```

Returns a list of image file paths. `num_batches * batch_size` controls the
number of generated images, and `seeds` must match that total.

### `generate_images_flax(...)`

Experimental Flax/JAX variant with the same overall intent. It is documented in
`sub-skills/generation/references/flax-and-tpu.md` because it needs a distinct
backend story.

## Audio and video utilities

### `get_timesteps_arr(...)`

```python
get_timesteps_arr(audio_filepath, offset, duration, fps=30, margin=1.0, smooth=0.0)
```

Loads audio with `librosa`, extracts percussive energy, and returns a 1D array
of interpolation weights. The helper is used to pace music videos.

### `make_video_pyav(...)`

```python
make_video_pyav(
    frames_or_frame_dir,
    audio_filepath=None,
    fps=30,
    audio_offset=0,
    audio_duration=2,
    sr=22050,
    output_filepath="output.mp4",
    glob_pattern="*.png",
)
```

Encodes a frame sequence or frame directory into an MP4. When `audio_filepath`
is supplied, the helper muxes audio into the output.

### `slerp(...)`

Spherical linear interpolation helper used by the walk pipeline.

### `pad_along_axis(...)`

Pads a NumPy array along the selected axis and is used by the Flax/TPU path.

## Upsampling

### `RealESRGANModel`

```python
RealESRGANModel(model_path, tile=0, tile_pad=10, pre_pad=0, fp32=False)
```

Key helpers:

- `RealESRGANModel.from_pretrained(model_name_or_path="nateraw/real-esrgan")`
- `RealESRGANModel.upsample_imagefolder(...)`
- `RealESRGANModel.forward(image, outscale=4, convert_to_pil=True)`

The model loader expects the `realesrgan` stack to be installed and may fetch a
checkpoint from Hugging Face Hub.

## UI

### `Interface`

```python
Interface(pipeline, params=None)
```

- `fn_images(...)` maps the image tab inputs to `generate_images(...)`.
- `fn_videos(...)` maps the video tab inputs to `pipeline.walk(...)`.
- `launch(*args, **kwargs)` forwards to the underlying Gradio interface.

## Hub helper

### `upload_folder_chunked(...)`

Uploads generated files to the Hugging Face Hub in file chunks. This is network
bound and should be treated as an opt-in workflow.
