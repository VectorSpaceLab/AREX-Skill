# Inference API Workflows

These workflows use the installed `sgm.inference.api` surface. They are planning and implementation patterns; constructing `SamplingPipeline` loads checkpoints and should only be done when the checkpoint/config pair and runtime device are ready.

## Safe Dry-Run Inspection

For API discovery without checkpoint loads:

```bash
python scripts/inspect_inference_api.py --json --assert-expected
```

The script imports `sgm.inference.api`, enumerates architectures, samplers, discretizations, guiders, `SamplingParams` defaults, signatures, and `model_specs`. It does not instantiate `SamplingPipeline` and does not open checkpoint files.

Use this pattern before GPU work:

1. Confirm the installed package imports.
2. Confirm expected enum values and checkpoint/config names.
3. Check that the selected `model_id` has a config and checkpoint name in `model_specs`.
4. Resolve `model_path` and `config_path` in the caller's project or environment, not inside the generated skill.
5. Only instantiate `SamplingPipeline` after files, optional dependencies, and device are known-good.

## SDXL Text-To-Image

Minimal plan:

```python
from sgm.inference.api import ModelArchitecture, SamplingParams, SamplingPipeline, Sampler

pipeline = SamplingPipeline(
    ModelArchitecture.SDXL_V1_BASE,
    model_path="checkpoints",
    config_path="configs/inference",
    device="cuda",
    use_fp16=True,
)

params = SamplingParams(
    width=1024,
    height=1024,
    steps=30,
    sampler=Sampler.DPMPP2M,
)
images = pipeline.text_to_image(
    params=params,
    prompt="A professional photograph of an astronaut riding a pig",
    negative_prompt="",
    samples=1,
)
```

Planning notes:

- `width` and `height` condition the sample shape as `(samples, 4, height // 8, width // 8)` before decoding.
- Use `Sampler.DPMPP2M` as a conservative default because it is the API default.
- Use `Discretization.EDM` only when the caller intentionally wants EDM sigmas and has selected appropriate `sigma_min`, `sigma_max`, and `rho`.
- `IdentityGuider` is available, but `VanillaCFG` with `scale=6.0` is the default guided path.

## SDXL Image-To-Image

Use `get_input_image_tensor` to make the input tensor from a PIL image:

```python
from PIL import Image
from sgm.inference.api import ModelArchitecture, SamplingParams, SamplingPipeline, Sampler
from sgm.inference.helpers import get_input_image_tensor

pipeline = SamplingPipeline(ModelArchitecture.SDXL_V1_BASE)
image = get_input_image_tensor(Image.open("input.png"), device="cuda")
params = SamplingParams(
    sampler=Sampler.DPMPP2M,
    steps=30,
    img2img_strength=0.65,
)
images = pipeline.image_to_image(
    params=params,
    image=image,
    prompt="A cinematic version of the input image",
    negative_prompt="low quality",
    samples=1,
)
```

Validation notes:

- The image tensor must be `[batch, channels, height, width]`, normally `[1, 3, H, W]`, scaled to `[-1, 1]`.
- `get_input_image_tensor` rounds width and height down to multiples of 64 before tensor conversion.
- Validate `0.0 <= img2img_strength <= 1.0` in caller code. The internal wrapper asserts this range only when strength is below `1.0`.
- Strength `1.0` means full sampling; smaller values prune the sigma schedule.

## SDXL Base Plus Refiner Handoff

Use `return_latents=True` on the base pipeline, then pass `samples_z` into the refiner. This mirrors the inference test behavior.

```python
from sgm.inference.api import ModelArchitecture, SamplingParams, SamplingPipeline, Sampler

base = SamplingPipeline(ModelArchitecture.SDXL_V1_BASE)
refiner = SamplingPipeline(ModelArchitecture.SDXL_V1_REFINER)
params = SamplingParams(sampler=Sampler.DPMPP2M, steps=30)

samples, samples_z = base.text_to_image(
    params=params,
    prompt="A detailed studio product photo",
    negative_prompt="blurry, low quality",
    samples=1,
    return_latents=True,
)

refined = refiner.refiner(
    params=params,
    image=samples_z,
    prompt="A detailed studio product photo",
    negative_prompt="blurry, low quality",
    samples=1,
)
```

Handoff rules:

- Pass the latent tensor `samples_z` to `refiner(..., image=samples_z)`, not the decoded `samples` tensor.
- Use matching SDXL version pairs: `SDXL_V1_BASE` with `SDXL_V1_REFINER`, or `SDXL_V0_9_BASE` with `SDXL_V0_9_REFINER`.
- Refiner computes original/target pixel dimensions as `image.shape[3] * 8` and `image.shape[2] * 8`, so latent shape matters.
- Refiner uses fixed aesthetic scores in its method body: `aesthetic_score=6.0`, `negative_aesthetic_score=2.5`.

## Choosing Sampler Settings

Suggested defaults and alternatives:

- Start with `Sampler.DPMPP2M`, `Discretization.LEGACY_DDPM`, `Guider.VANILLA`, and `scale=6.0` for SDXL parity with API defaults.
- Use `EulerEDMSampler` or `HeunEDMSampler` when experimenting with EDM-style schedules and expose `s_churn`, `s_tmin`, `s_tmax`, and `s_noise`.
- Use `EulerAncestralSampler` or `DPMPP2SAncestralSampler` when the caller wants ancestral noise controls through `eta` and `s_noise`.
- Use `LinearMultistepSampler` when the caller needs `order`; default `order=4`.
- Pair `Discretization.EDM` with explicit `sigma_min`, `sigma_max`, and `rho`; otherwise stay with `LegacyDDPMDiscretization`.

## Checkpoint And Config Validation Pattern

Before constructing a pipeline in production code, validate expected files from `model_specs`:

```python
from pathlib import Path
from sgm.inference.api import ModelArchitecture, model_specs

model_id = ModelArchitecture.SDXL_V1_BASE
spec = model_specs[model_id]
config_file = Path(config_path) / spec.config
ckpt_file = Path(model_path) / spec.ckpt
if not config_file.exists():
    raise FileNotFoundError(f"Missing SDXL config: {spec.config}")
if not ckpt_file.exists():
    raise FileNotFoundError(f"Missing SDXL checkpoint: {spec.ckpt}")
```

Prefer this early check when diagnosing `OmegaConf.load` failures, `load_model_from_config` errors, or `load_state_dict` missing/unexpected keys.

## CPU-Only Planning Pattern

In CPU-only environments, avoid constructing `SamplingPipeline` unless the user explicitly wants to debug model loading on CPU and accepts the limits. The API defaults are CUDA-oriented: constructor default `device="cuda"`, helper defaults of `device="cuda"`, and public sampling methods do not forward the constructor device into `do_sample`, `do_img2img`, or `get_batch`. Use the bundled inspection script and enum/spec tables for planning, then hand off a GPU-ready command or an explicitly patched/wrapped CPU experiment for actual sampling.
