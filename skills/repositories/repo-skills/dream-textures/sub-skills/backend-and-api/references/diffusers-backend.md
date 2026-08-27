# DiffusersBackend and Generator Internals

This reference covers Dream Textures' default local backend, source-backed scheduler/device/model handling, and the model/task compatibility logic future agents usually need for diagnosis.

## Default backend identity and registration

`DiffusersBackend` is the default registered backend.

```python
class DiffusersBackend(Backend):
    name = "HuggingFace Diffusers"
    description = "Local image generation inside of Blender"
```

The add-on registers `DiffusersBackend` during Blender add-on registration. Custom backends should not modify the default class; they should register their own `Backend` subclass.

## Model and scheduler lists

`DiffusersBackend.list_models(context)` reads `StableDiffusionPreferences.installed_models` and returns `api.Model` rows:

- `name`: cache-style names such as `models--org--repo` are displayed as `org/repo`.
- `description`: `ModelType[model.model_type].name`.
- `id`: same normalized `org/repo` value used later by `checkpoint_lookup` / `model_lookup`.
- Models with `ModelType.CONTROL_NET` or `ModelType.UNKNOWN` are excluded from the main list.
- Groups are sorted by model type and separated with `None` entries for Blender enum separators.

`DiffusersBackend.list_controlnet_models(context)` returns only installed models whose type is `CONTROL_NET`, with description `ControlNet`.

`DiffusersBackend.list_schedulers(context)` returns these `Scheduler.value` strings:

```text
DDIM
DDPM
DEIS Multistep
DPM Solver Multistep
DPM Solver Multistep Karras
DPM Solver Singlestep
DPM Solver Singlestep Karras
Euler Discrete
Euler Discrete Karras
Euler Ancestral Discrete
Heun Discrete
Heun Discrete Karras
KDPM2 Discrete
KDPM2 Ancestral Discrete
LMS Discrete
LMS Discrete Karras
PNDM
UniPC Multistep
```

`Scheduler.create(pipeline)` maps those enum values to Diffusers scheduler classes and preserves the pipeline scheduler's original config as `_original_config`. Karras variants pass `use_karras_sigmas=True` when constructing from config.

## Optimization dataclass and UI properties

Verified `Optimizations` signature:

```python
Optimizations(
    attention_slicing: bool = True,
    attention_slice_size: str | int = "auto",
    cudnn_benchmark: bool = False,        # cuda-only
    tf32: bool = False,                   # cuda-only
    amp: bool = False,                    # cuda-only dataclass option, not exposed by DiffusersBackend UI
    half_precision: bool = True,          # cuda/dml
    cpu_offload: str | CPUOffload = CPUOffload.OFF,  # cuda/dml
    channels_last_memory_format: bool = False,
    sdp_attention: bool = True,
    batch_size: int = 1,
    vae_slicing: bool = True,
    vae_tiling: str = "off",
    vae_tile_size: int = 512,
    vae_tile_blend: int = 64,
    cfg_end: float = 1.0,
    cpu_only: bool = False,
) -> None
```

`CPUOffload` values are `off`, `model`, and `submodule`.

`DiffusersBackend.optimizations()` creates `Optimizations()`, copies same-named Blender properties from the backend instance, normalizes `attention_slice_size="auto"` when `attention_slice_size_src == "auto"`, and converts `cpu_offload` to `CPUOffload`.

`Optimizations.apply(pipeline, device)` performs best-effort modifications and intentionally suppresses exceptions for broad pipeline compatibility:

- Moves the pipeline to the selected device unless CPU offload is active.
- Sets cuDNN benchmark and TF32 flags when supported.
- Uses SDP attention if enabled; otherwise attention slicing; otherwise disables attention slicing.
- Enables model or submodule CPU offload with `accelerate` when selected.
- Applies channels-last memory format when requested.
- Enables VAE slicing and optional VAE tiled decode patching.
- Enables Dream Textures DirectML patches on `dml`; disables them otherwise.

Half precision is considered usable on CUDA except for GTX 1650/1660 GPUs; on DirectML it follows the `half_precision` flag.

## Device selection order

`Generator.choose_device(optimizations)` returns:

1. `cpu` immediately when `optimizations.cpu_only` is true.
2. `cuda` when `torch.cuda.is_available()` is true.
3. `mps` when `torch.backends.mps.is_available()` is true.
4. `dml` when `torch_directml` is importable and available; it also renames PyTorch privateuse1 backend to `dml`.
5. `cpu` fallback.

Do not use a CPU-only import smoke as proof that CUDA, ROCm, MPS, or DirectML generation works; full generation requires Blender, backend dependencies, and model assets.

## Task routing in `DiffusersBackend.generate()`

The backend builds common keyword arguments from `GenerationArguments`:

```python
common_kwargs = {
    "model": checkpoint_lookup.get(arguments.model.id),
    "scheduler": Scheduler(arguments.scheduler),
    "optimizations": self.optimizations(),
    "prompt": arguments.prompt.positive,
    "steps": arguments.steps,
    "width": arguments.size[0] if arguments.size is not None else None,
    "height": arguments.size[1] if arguments.size is not None else None,
    "seed": arguments.seed,
    "cfg_scale": arguments.guidance_scale,
    "use_negative_prompt": arguments.prompt.negative is not None,
    "negative_prompt": arguments.prompt.negative or "",
    "seamless_axes": arguments.seamless_axes,
    "iterations": arguments.iterations,
    "step_preview_mode": arguments.step_preview_mode,
    "sdxl_refiner_model": checkpoint_lookup.get(self.sdxl_refiner_model) if self.use_sdxl_refiner else None,
}
```

Routing by task:

| `arguments.task` | Generator action | Notes |
| --- | --- | --- |
| `PromptToImage()` | `gen.prompt_to_image(**common_kwargs)` | With `control_nets`, routes to `gen.control_net(..., image=None, inpaint=False, strength=1)`. |
| `Inpaint(...)` | `gen.inpaint(...)` | With `control_nets`, routes to `gen.control_net(..., image=image, inpaint=True)` and maps mask source to `alpha` or `prompt`. |
| `ImageToImage(...)` | `gen.image_to_image(image=image, fit=fit, strength=strength, ...)` | With `control_nets`, routes to `gen.control_net(..., image=image, inpaint=False)`. |
| `DepthToImage(...)` | `gen.depth_to_image(depth=depth, image=image, strength=strength, ...)` | If no depth map is supplied, the depth action may load a DPT depth estimator. |
| `Outpaint(...)` | `gen.outpaint(image=image, outpaint_origin=origin, fit=False, strength=1, inpaint_mask_src="alpha", ...)` | Outpaint builds an RGBA inpaint tile and delegates to `inpaint`. |
| `Upscale(...)` | `gen.upscale(image=image, tile_size=tile_size, blend=blend, ...)` | The upscaling operator bypasses normal `validate()` and overwrites `generated_args.task`. |
| other | raises `NotImplementedError` | Custom tasks require custom backend support. |

After dispatch, `DiffusersBackend` wires `Future` callbacks:

- Generator responses call `step_callback(step_image)`.
- If the step callback returns `False`, the future is cancelled and `callback(InterruptedError())` is called.
- Completion calls `callback(future.result(last_only=True))`.
- Exceptions call `callback(exception)`.

## Model type and task compatibility

`ModelType` is inferred mostly from U-Net `in_channels` for cached models and from checkpoint config choice for linked checkpoints.

| ModelType | Value | Recommended model | Tasks accepted by `matches_task()` |
| --- | ---: | --- | --- |
| `UNKNOWN` | `0` | `stabilityai/stable-diffusion-2-1` | none |
| `PROMPT_TO_IMAGE` | `4` | `stabilityai/stable-diffusion-2-1` | `PromptToImage`, `ImageToImage` |
| `DEPTH` | `5` | `stabilityai/stable-diffusion-2-depth` | `DepthToImage` |
| `UPSCALING` | `7` | `stabilityai/stable-diffusion-x4-upscaler` | not accepted by `matches_task()` in this version |
| `INPAINTING` | `9` | `stabilityai/stable-diffusion-2-inpainting` | `Inpaint`, `Outpaint` |
| `CONTROL_NET` | `-1` | `stabilityai/stable-diffusion-2-1` | not a main generation model |
| `UNSPECIFIED_CHECKPOINT` | `-2` | `stabilityai/stable-diffusion-2-1` | accepts all tasks in `matches_task()` |

`DiffusersBackend.validate(arguments)`:

- Raises `FixItError("No model selected.", FixItError.ChangeProperty("model"))` when no model is selected.
- For model/task mismatch, raises `FixItError` with either a download suggestion for the recommended model type or a `ChangeProperty("model")` selector fix.
- Does not validate `Upscale` correctly through `ModelType.matches_task()` in this version; the bundled upscaling operator calls `generate()` directly after changing the task.

## Model configs and checkpoint loading

`ModelConfig` values used for checkpoint linking/import/conversion:

```text
AUTO_DETECT = auto-detect
STABLE_DIFFUSION_1 = v1
STABLE_DIFFUSION_2_BASE = v2 (512, epsilon)
STABLE_DIFFUSION_2 = v2 (768, v_prediction)
STABLE_DIFFUSION_2_DEPTH = v2 (depth)
STABLE_DIFFUSION_2_INPAINTING = v2 (inpainting)
STABLE_DIFFUSION_XL_BASE = XL (base)
STABLE_DIFFUSION_XL_REFINER = XL (refiner)
CONTROL_NET_1_5 = 1.5 (ControlNet)
CONTROL_NET_2_1 = 2.1 (ControlNet)
```

`ModelConfig.original_config` maps these to bundled Stable Diffusion YAML configs. `ModelConfig.pipeline` maps checkpoint conversion/loading to the appropriate Diffusers pipeline or `ControlNetModel`.

`load_model()` behavior:

- Selects device, computes half precision, and invalidates the pipeline cache when `(device, half_precision, cpu_offload, has_controlnet)` changes.
- Removes unused cached models, refiner models, and stale ControlNet containers.
- For ControlNet, wraps one or more ControlNet models in `MultiControlNetModel`.
- For `.ckpt` / `.safetensors` / `Checkpoint`, uses `from_single_file()` when available or Diffusers checkpoint conversion helpers otherwise.
- For Hugging Face cache entries, accepts `main` and `fp16` revisions and tries fp16/fp32 strategies with warning fallbacks.
- If `scheduler` is a string at this low level, it expects an enum name such as `DPM_SOLVER_MULTISTEP`, not the UI display value. `DiffusersBackend` avoids this by passing `Scheduler(arguments.scheduler)` first.

## SDXL refiner behavior

`prompt_to_image()` only attempts SDXL refiner logic for CUDA. If enough GPU memory is available or CPU offload is enabled, it loads base and refiner together. Otherwise it generates base latents first, releases the base pipe, then loads the refiner. If the loaded base pipeline is not `StableDiffusionXLPipeline`, `load_model()` returns `(pipe, None)` for the refiner branch and clears incompatible refiner cache entries.

## Source-level action details

- Prompt/image/inpaint/depth/control actions create a `torch.Generator`; MPS and DirectML use a CPU generator because those backends do not support the PyTorch `Generator` API.
- Width/height defaults usually come from `pipe.unet.config.sample_size * pipe.vae_scale_factor`; depth and ControlNet paths hard-code a 512 default and round to multiples of 8 for image inputs.
- `SeamlessAxes.AUTO` may call the seamless detector from source/control/depth images and then patch U-Net/VAE convolution padding for circular tiling.
- Prompt-mask inpainting and ControlNet prompt masks load CLIPSeg (`CIDAS/clipseg-rd64-refined`) through `transformers` when selected.
- Depth generation with no depth map can load `Intel/dpt-large` through `transformers`.
