# API Reference

## Purpose

Read this when a task needs the Python API instead of a command-line recipe. These signatures were verified from the prepared inspection environment and are bundled in this skill under `runtime/pipelines/` without requiring the original checkout.

## Main pipeline wrapper

```python
InfUFluxPipeline(
    base_model_path,
    infu_model_path,
    insightface_root_path="./",
    image_proj_num_tokens=8,
    infu_flux_version="v1.0",
    model_version="aes_stage2",
    quantize_8bit=False,
    cpu_offload=False,
)
```

Important constructor parameters:

| Parameter | Meaning |
| --- | --- |
| `base_model_path` | Local FLUX base model directory or a Hugging Face repo id such as `black-forest-labs/FLUX.1-dev`. |
| `infu_model_path` | Directory for one InfiniteYou variant, for example a path ending in `infu_flux_v1.0/aes_stage2`. |
| `insightface_root_path` | Root containing InsightFace support files. |
| `image_proj_num_tokens` | Number of image-projection query tokens. Default is `8`; checkpoint shapes must match changes. |
| `infu_flux_version` | Repository snapshot supports `v1.0`. |
| `model_version` | `aes_stage2` or `sim_stage1`. |
| `quantize_8bit` | Quantizes InfuseNet, transformer, and `text_encoder_2` using optimum-quanto before assembly. |
| `cpu_offload` | Avoids moving the whole Diffusers pipeline to CUDA at construction and uses staged movement later. |

## Call signature

```python
image = pipe(
    id_image,                         # PIL.Image.Image RGB
    prompt,                           # str
    control_image=None,               # optional PIL.Image.Image RGB
    width=864,
    height=1152,
    seed=42,
    guidance_scale=3.5,
    num_steps=30,
    infusenet_conditioning_scale=1.0,
    infusenet_guidance_start=0.0,
    infusenet_guidance_end=1.0,
    cpu_offload=False,
)
```

Return value: a single `PIL.Image.Image` generated image.

## Minimal API pattern

```python
from pathlib import Path
import sys
from PIL import Image

# When running this manual API pattern from the generated skill directory,
# add the bundled implementation package. The bundled scripts do this automatically.
skill_dir = Path(".").resolve()
sys.path.insert(0, str(skill_dir / "runtime"))
from pipelines.pipeline_infu_flux import InfUFluxPipeline

model_dir = Path("models/InfiniteYou")
pipe = InfUFluxPipeline(
    base_model_path="models/FLUX.1-dev",
    infu_model_path=str(model_dir / "infu_flux_v1.0" / "aes_stage2"),
    insightface_root_path=str(model_dir / "supports" / "insightface"),
    infu_flux_version="v1.0",
    model_version="aes_stage2",
    quantize_8bit=True,
    cpu_offload=True,
)
image = pipe(
    id_image=Image.open("id.jpg").convert("RGB"),
    prompt="A person, portrait, cinematic",
    control_image=None,
    seed=1234,
    guidance_scale=3.5,
    num_steps=30,
    infusenet_conditioning_scale=1.0,
    infusenet_guidance_start=0.0,
    infusenet_guidance_end=1.0,
    cpu_offload=True,
)
image.save("result.png")
```

## Identity and control image behavior

- `id_image` is converted from RGB PIL to BGR NumPy before face analysis.
- The largest detected face is selected when multiple faces are present.
- If no identity face is detected, the pipeline raises `ValueError('No face detected in the input ID image')`.
- If `control_image` is provided, it is converted to RGB, resized/padded to `(width, height)`, and face keypoints are drawn as a control condition.
- If no control image is provided, the code creates a black control image with the requested height and width.
- If no face is detected in a provided control image, the pipeline raises `ValueError('No face detected in the control image')`.

## Guidance parameter mapping

The outer API exposes InfiniteYou names and maps them into the Diffusers controlnet call:

| Outer parameter | Inner parameter |
| --- | --- |
| `guidance_scale` | `guidance_scale` for text conditioning. |
| `infusenet_conditioning_scale` | `controlnet_conditioning_scale`. |
| `infusenet_guidance_start` | `control_guidance_start`. |
| `infusenet_guidance_end` | `control_guidance_end`. |
| fixed value | `controlnet_guidance_scale=1.0`. |
| identity embedding | `controlnet_prompt_embeds`. |

## Practical API constraints

- The generated skill bundles this API under `runtime/pipelines/`; add that `runtime/` directory to `sys.path` when calling the API manually outside the bundled scripts.
- Constructor and call paths hard-code several CUDA moves. Treat CUDA as required for generation.
- The code uses `torch.bfloat16` for loaded FLUX/InfuseNet modules.
- `--cpu-offload`/`cpu_offload=True` reduces CUDA memory pressure but still stages work onto CUDA.
- Model access errors may occur during constructor calls when local paths are missing or the FLUX gated model is not accessible.
- Optional LoRAs are loaded through `pipe.load_loras(loras)`, where each row is `[path, adapter_name, scale]`.
