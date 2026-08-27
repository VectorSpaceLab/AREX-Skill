# Pipeline Workflows

This reference distills common Diffusers inference workflows. It is written for coding agents that need to produce safe, realistic pipeline code without reopening the source repository.

## Choose the Pipeline Surface

| Task | Preferred class family | Required call inputs | Notes |
| --- | --- | --- | --- |
| Text-to-image | `AutoPipelineForText2Image` or a model-specific pipeline | `prompt` | Use `DiffusionPipeline` when preserving an existing model repo's declared pipeline type is more important than task routing. |
| Image-to-image | `AutoPipelineForImage2Image` or a model-specific img2img pipeline | `prompt`, `image`, often `strength` | `strength` controls how strongly the initial image is transformed. |
| Inpainting | `AutoPipelineForInpainting` or a model-specific inpaint pipeline | `prompt`, `image`, `mask_image` | Keep image and mask aligned in size/mode; white mask regions are typically regenerated. |
| ControlNet | ControlNet model plus a ControlNet pipeline | `prompt`, `image` or `control_image`, optional `controlnet_conditioning_scale` | Some families name the conditioning image `image`; SD3/Flux variants often use `control_image`. Check the concrete pipeline signature. |
| T2I-Adapter | Adapter model plus an adapter pipeline | `prompt`, `image` | Multi-adapter calls pass lists of adapters/images and matching conditioning scales. |
| Batched generation | Same pipeline as single generation | list-valued prompts/images plus list of generators | Batch size increases memory and latency; use one generator per batch item. |
| Server inference | Shared loaded pipeline plus per-request clone/generator | request prompt and per-request seed/generator | Clone the scheduler/pipeline per concurrent request because schedulers are mutable during denoising. |

## Text-to-Image Skeleton

```python
import torch
from diffusers import AutoPipelineForText2Image

model_id = "org/model-or-local-path"
device = "cuda" if torch.cuda.is_available() else "cpu"
dtype = torch.float16 if device == "cuda" else torch.float32

pipe = AutoPipelineForText2Image.from_pretrained(
    model_id,
    torch_dtype=dtype,
    local_files_only=True,
)
pipe = pipe.to(device)

generator = torch.Generator(device="cpu").manual_seed(0)
result = pipe(
    prompt="a precise prompt",
    negative_prompt="low quality, blurry",
    num_inference_steps=25,
    generator=generator,
)
image = result.images[0]
```

Use `device_map="cuda"`, `device_map="auto"`, or `device_map="balanced"` instead of a final `.to(device)` when relying on Accelerate placement. Do not combine a pipeline already loaded with a device map with an unconditional `.to("cuda")` unless you intentionally reset placement.

## Image-to-Image

```python
from diffusers import AutoPipelineForImage2Image
from diffusers.utils import load_image

pipe = AutoPipelineForImage2Image.from_pretrained(model_id, torch_dtype=dtype, local_files_only=True).to(device)
init_image = load_image("/path/to/input.png").convert("RGB")
result = pipe(
    prompt="make the scene cinematic",
    image=init_image,
    strength=0.75,
    guidance_scale=7.5,
    generator=torch.Generator(device="cpu").manual_seed(123),
)
```

Guidelines:

- Use `strength` in the pipeline-supported range, commonly `0.0` to `1.0`.
- If batching, pass `prompt=[...]`, `image=[...]`, and `generator=[torch.Generator(device="cpu").manual_seed(seed) for seed in seeds]`.
- Keep PIL images in RGB unless the concrete pipeline expects tensors or another mode.

## Inpainting

```python
from diffusers import AutoPipelineForInpainting
from diffusers.utils import load_image

pipe = AutoPipelineForInpainting.from_pretrained(model_id, torch_dtype=dtype, local_files_only=True).to(device)
image = load_image("/path/to/base.png").convert("RGB")
mask = load_image("/path/to/mask.png").convert("RGB")

if image.size != mask.size:
    raise ValueError(f"image and mask_image must have the same size, got {image.size} and {mask.size}")

result = pipe(
    prompt="replace the masked region with a vase of flowers",
    image=image,
    mask_image=mask,
    height=image.height,
    width=image.width,
    generator=torch.Generator(device="cpu").manual_seed(7),
)
```

Inpainting failure prevention:

- Match `image` and `mask_image` size before calling the pipeline.
- Avoid `torch.float16` on CPU; use float32 on CPU and reserve fp16/bfloat16 for supported accelerators.
- If the prompt/model is gated or private, ensure the user's Hugging Face token/login is available before any download. For offline mode, use a local snapshot path and `local_files_only=True`.
- Some inpainting/control variants round output dimensions down to multiples of the model's VAE scale factor; pass supported `height`/`width` explicitly when exact dimensions matter.

## Control-Conditioned Generation

Control workflows add one or more conditioning modules or images to a base pipeline. Keep adapter mechanics in the adapters sub-skill; at pipeline-call level, wire the input names correctly.

### ControlNet

```python
import torch
from diffusers import ControlNetModel, StableDiffusionControlNetPipeline

controlnet = ControlNetModel.from_pretrained(controlnet_id, torch_dtype=dtype, local_files_only=True)
pipe = StableDiffusionControlNetPipeline.from_pretrained(
    base_model_id,
    controlnet=controlnet,
    torch_dtype=dtype,
    local_files_only=True,
).to(device)

result = pipe(
    prompt="a detailed architectural rendering",
    image=control_image,
    controlnet_conditioning_scale=0.8,
    generator=torch.Generator(device="cpu").manual_seed(42),
)
```

For SD3/Flux ControlNet pipelines, the image argument may be `control_image` instead of `image`. Multi-ControlNet calls commonly pass lists for `control_image`/`image` and matching `controlnet_conditioning_scale` values.

### T2I-Adapter

```python
from diffusers import StableDiffusionXLAdapterPipeline, T2IAdapter

adapter = T2IAdapter.from_pretrained(adapter_id, torch_dtype=dtype, local_files_only=True)
pipe = StableDiffusionXLAdapterPipeline.from_pretrained(
    base_model_id,
    adapter=adapter,
    torch_dtype=dtype,
    local_files_only=True,
).to(device)
result = pipe(prompt="a rabbit in a garden", image=condition_image, generator=generator)
```

## Batched Inference

```python
prompts = ["a red fox", "a blue bird", "a green turtle"]
generators = [torch.Generator(device="cpu").manual_seed(seed) for seed in [0, 1, 2]]
result = pipe(prompts, generator=generators, num_images_per_prompt=1)
images = result.images
```

Rules:

- Batch prompt-like fields together: if `prompt` is a list, `negative_prompt`, images, masks, and control images should be scalar-broadcastable or matching lists supported by that pipeline.
- Do not use `[torch.Generator(...)] * batch_size`; that repeats the same generator object and consumes its state sequentially.
- `num_images_per_prompt` multiplies output count by prompt batch size.
- Use smaller batches or CPU/model offload when hitting out-of-memory errors.

## Callbacks and Step Hooks

Diffusers pipelines commonly support `callback_on_step_end` and `callback_on_step_end_tensor_inputs` for denoising-step hooks.

```python
def inspect_or_stop(pipe, step_index, timestep, callback_kwargs):
    latents = callback_kwargs.get("latents")
    if step_index >= 10:
        pipe._interrupt = True
    return callback_kwargs

result = pipe(
    prompt="a product photo",
    callback_on_step_end=inspect_or_stop,
    callback_on_step_end_tensor_inputs=["latents"],
)
```

Callback rules:

- Signature is usually `(pipe, step_index, timestep, callback_kwargs)`.
- Return the callback kwargs dictionary, including any tensors you mutate.
- Only request names supported by the concrete pipeline's `_callback_tensor_inputs`.
- Use callbacks for monitoring, early interruption, or controlled tensor edits; avoid heavyweight image decoding every step in production unless profiling shows it is acceptable.

## Serving Pattern

Use one shared loaded pipeline to avoid reloading weights, but isolate mutable per-request state.

```python
import asyncio
import random
import torch

async def generate(shared_pipeline, prompt):
    loop = asyncio.get_event_loop()
    scheduler = shared_pipeline.scheduler.from_config(shared_pipeline.scheduler.config)
    request_pipe = shared_pipeline.__class__.from_pipe(shared_pipeline, scheduler=scheduler)
    generator = torch.Generator(device=shared_pipeline.device).manual_seed(random.randint(0, 10_000_000))
    return await loop.run_in_executor(None, lambda: request_pipe(prompt, generator=generator))
```

Serving rules:

- Clone or recreate the scheduler for concurrent requests; scheduler state changes during denoising and is not thread-safe.
- Use one generator per request.
- Load the model at process startup, not per request.
- Keep request validation outside the pipeline call: prompt type, size limits, seed range, batch size, and local/offline model policy.
