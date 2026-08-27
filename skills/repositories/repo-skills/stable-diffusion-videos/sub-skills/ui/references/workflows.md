# UI workflows

Use this page when you need to launch or explain the package's Gradio interface.

## Basic `Interface` usage

The public UI shape is:

```python
from stable_diffusion_videos import StableDiffusionWalkPipeline, Interface
import torch

pipe = StableDiffusionWalkPipeline.from_pretrained(
    "CompVis/stable-diffusion-v1-4",
    torch_dtype=torch.float16,
).to("cuda")

interface = Interface(pipe)
interface.launch()
```

`Interface` builds two tabs:

- **Images!** calls `fn_images(...)`, which forwards to `generate_images(...)`.
- **Videos!** calls `fn_videos(...)`, which parses newline-separated prompts and
  seeds, then forwards to `pipeline.walk(...)`.

If `params` is provided, the class assumes a Flax pipeline and forwards those
parameters into the generation calls.

## Adapted launcher

The bundled `../scripts/launch_interface.py` is a safer form of the repository's
simple launcher.

From the root skill directory, dry-run first:

```bash
python sub-skills/ui/scripts/launch_interface.py --dry-run
```

Launch when ready:

```bash
python sub-skills/ui/scripts/launch_interface.py \
  --model-id runwayml/stable-diffusion-v1-5 \
  --vae-id stabilityai/sd-vae-ft-mse \
  --scheduler lms \
  --device cuda \
  --dtype float16 \
  --safety-checker-none \
  --run
```

The dry run prints what would be loaded without importing model weights or
starting a server.

## Mapping from UI controls to package APIs

### Image tab

The image tab forwards these values to `generate_images(...)`:

- prompt
- batch size
- number of batches
- inference steps
- guidance scale
- height and width
- upsample toggle
- output directory

It returns gallery entries from generated image paths.

### Video tab

The video tab forwards these values to `pipeline.walk(...)`:

- newline-separated prompts
- newline-separated seeds
- interpolation steps
- FPS
- batch size
- inference steps
- guidance scale
- height and width
- upsample toggle
- output directory

It returns the generated video path.

## Experimental music-video UI

The source example contains a richer music-video UI with audio slicing,
percussive-weight plotting, image preview, and a final generation button. It is
reference-only in this skill because it also:

- loads a CUDA model at import time,
- can use network access to download an example audio clip,
- depends on extra packages such as `youtube_dl`, `soundfile`, and `matplotlib`,
- starts an interactive Gradio process.

For non-interactive or safer workflows, use the generation sub-skill helpers:

- `sub-skills/generation/scripts/preview_audio_timesteps.py`
- `sub-skills/generation/scripts/make_video_template.py`
