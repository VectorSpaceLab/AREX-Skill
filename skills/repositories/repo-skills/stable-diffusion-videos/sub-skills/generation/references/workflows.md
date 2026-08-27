# Generation workflows

Use this page when you need a concrete recipe for prompt walks, audio-paced
interpolation, still-image batches, or optional upsampling.

## 1) Prompt walk video

The core workflow is `StableDiffusionWalkPipeline.walk(...)`.

Typical shape:

```python
from stable_diffusion_videos import StableDiffusionWalkPipeline
import torch

pipe = StableDiffusionWalkPipeline.from_pretrained(
    "CompVis/stable-diffusion-v1-4",
    torch_dtype=torch.float16,
).to("cuda")

video_path = pipe.walk(
    prompts=["a cat", "a dog"],
    seeds=[42, 1337],
    num_interpolation_steps=3,
    output_dir="dreams",
    name="animals_test",
    fps=30,
    guidance_scale=8.5,
    num_inference_steps=50,
)
```

Key rules:

- `prompts` and `seeds` must line up.
- If `num_interpolation_steps` is an `int`, it is expanded for each prompt gap.
- `height` and `width` must be multiples of 8.
- `make_video=True` writes MP4 output under `output_dir/name/`.
- `resume=True` reuses `prompt_config.json` in the named output directory.

Expected output tree:

```text
output_dir/
  name/
    prompt_config.json
    name_000000/
      frame000000.png
      ...
      name_000000.mp4
    name_000001/
      ...
    name.mp4
```

## 2) Music-synced video

For audio-paced interpolation, convert offsets into interpolation steps:

```python
audio_offsets = [146, 148]
fps = 30
num_interpolation_steps = [(b - a) * fps for a, b in zip(audio_offsets, audio_offsets[1:])]
```

Then pass:

- `audio_filepath` to the audio file
- `audio_start_sec=audio_offsets[0]`
- `fps` to control the conversion from seconds to frames
- `margin` and `smooth` to shape the interpolation weights

The bundled `scripts/preview_audio_timesteps.py` helps you check the weight curve
before you launch a long run.

## 3) Still-image batches

Use `generate_images(...)` when you want prompt-conditioned image batches rather
than a walk.

Typical shape:

```python
from stable_diffusion_videos import StableDiffusionWalkPipeline, generate_images

paths = generate_images(
    pipeline=pipe,
    prompt="blueberry spaghetti",
    batch_size=4,
    num_batches=2,
    seeds=[1, 2, 3, 4, 5, 6, 7, 8],
    output_dir="images",
    name="blueberry_batch",
)
```

Notes:

- The number of seeds must equal `batch_size * num_batches`.
- `upsample=True` loads the Real-ESRGAN model lazily if it is not already on the
  pipeline object.
- `push_to_hub=True` is network-bound and requires `repo_id`.

## 4) Upsampling

Use `RealESRGANModel.from_pretrained(...)` only when you need the 4x upsampling
path.

```python
from stable_diffusion_videos import RealESRGANModel
model = RealESRGANModel.from_pretrained("nateraw/real-esrgan")
```

Useful helper:

- `model.upsample_imagefolder(in_dir, out_dir, recursive=False, force=False)`

## 5) Helper scripts

- `../scripts/make_video_template.py` converts the music-video recipe into a safer
  command-line helper with `--dry-run` and `--run` modes.
- `../scripts/preview_audio_timesteps.py` prints a compact summary of the audio
  interpolation weights.
- `../../../scripts/check_env.py` validates imports and tiny backend smokes before a
  longer run.

## 6) Optional Hub upload

`upload_folder_chunked(...)` uploads an output directory in file groups. Treat
this as an explicit opt-in because it is network-bound and can create or update
remote content.
