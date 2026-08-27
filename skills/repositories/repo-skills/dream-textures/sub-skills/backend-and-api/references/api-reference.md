# Dream Textures Backend API Reference

This reference distills the public backend surface verified from Dream Textures source and safe package inspection. It is self-contained; use source-relative filenames only as provenance labels, not as runtime dependencies.

## Backend base class contract

`dream_textures.api.Backend` is defined as a subclass of `bpy.types.PropertyGroup`. Blender class registration is expected to attach backend instances to `DreamPrompt` via a pointer property named from the backend class id.

Callback aliases from `api/backend/backend.py`:

```python
StepCallback = Callable[[List[GenerationResult]], bool]
Callback = Callable[[List[GenerationResult] | Exception], None]
```

Current method signatures:

```python
Backend.register(cls) -> None
Backend.unregister(cls) -> None
Backend._id(cls) -> str
Backend._attribute(cls) -> str
Backend._lookup(cls, id)
Backend._list_backends(cls)

Backend.list_models(self, context) -> List[Model]
Backend.list_controlnet_models(self, context) -> List[Model]
Backend.list_schedulers(self, context) -> List[str]
Backend.draw_prompt(self, layout, context) -> None
Backend.draw_advanced(self, layout, context) -> None
Backend.draw_speed_optimizations(self, layout, context) -> None
Backend.draw_memory_optimizations(self, layout, context) -> None
Backend.draw_extra(self, layout, context) -> None
Backend.get_batch_size(self, context) -> int
Backend.generate(self, arguments: GenerationArguments, step_callback: StepCallback, callback: Callback) -> None
Backend.validate(self, arguments: GenerationArguments) -> None
```

Important contract details:

- `list_models()` returns `Model` choices consumed by `GenerationArguments.model`; `Model.id` is the stable value passed back to `generate()`.
- `list_controlnet_models()` defaults to `[]`; implement it only when the backend supports ControlNet choices.
- `list_schedulers()` returns display strings accepted by that backend. For `DiffusersBackend`, these strings are `Scheduler.value` values, not enum names.
- `get_batch_size()` defaults to `1`; `DreamPrompt.generate_args()` uses it for file-batch prompt slicing.
- `generate()` must eventually call `callback(...)` with either `list[GenerationResult]` or an `Exception`.
- If `step_callback(progress)` returns `False`, cancel generation and call `callback(InterruptedError())`.
- `validate()` must be fast. Raise `ValueError` for ordinary invalid input or `FixItError` to present a UI fix.

## Public dataclasses

Verified constructor signatures:

```python
GenerationArguments(
    task: Task,
    model: Model,
    prompt: Prompt,
    size: tuple[int, int] | None,
    seed: int,
    steps: int,
    guidance_scale: float,
    scheduler: str,
    seamless_axes: SeamlessAxes,
    step_preview_mode: StepPreviewMode,
    iterations: int,
    control_nets: list[ControlNet],
) -> None

Prompt(positive: str | list[str], negative: str | list[str] | None) -> None
Model(name: str, description: str, id: str) -> None
ControlNet(model: str, image: NDArray, strength: float) -> None
GenerationResult(progress: int, total: int, seed: int, title: str | None = None, image: NDArray | None = None) -> None
```

Inspection note: this Dream Textures release imports `ControlNet` inside `generation_arguments.py`, but `api.models.__init__` does not re-export it. Import it from `dream_textures.api.models.control_net` when direct access is needed.

`GenerationArguments._map_property_name(name)` maps API fields back to `DreamPrompt` UI properties for validation/UI fixes. Known mappings include `model`, `prompt`, `prompt.positive`, `prompt.negative`, `size`, `seed`, `steps`, `guidance_scale`, `scheduler`, `seamless_axes`, `step_preview_mode`, and `iterations`.

`GenerationResult.image` is a NumPy array shaped `(height, width, channels)` with 3 or 4 channels. `GenerationResult.tile_images(results)` returns one image, a centered grid of multiple result images, or `None` if no images are present.

## Task dataclasses

`GenerationArguments.task` is one of these dataclass task values. Prefer structural pattern matching or `isinstance()` checks rather than string names.

```python
PromptToImage() -> None
ImageToImage(image: NDArray, strength: float, fit: bool) -> None
Inpaint(image: NDArray, strength: float, fit: bool, mask_source: Inpaint.MaskSource, mask_prompt: str, confidence: float) -> None
DepthToImage(depth: NDArray | None, image: NDArray | None, strength: float) -> None
Outpaint(image: NDArray, origin: tuple[int, int]) -> None
Upscale(image: NDArray, tile_size: int, blend: int) -> None
```

Human-readable `Task.name()` values:

| Task class | `name()` |
| --- | --- |
| `PromptToImage` | `prompt to image` |
| `ImageToImage` | `image to image` |
| `Inpaint` | `inpainting` |
| `DepthToImage` | `depth to image` |
| `Outpaint` | `outpainting` |
| `Upscale` | `upscaling` |

`Inpaint.MaskSource` values:

| Name | Value | Meaning |
| --- | ---: | --- |
| `ALPHA` | `0` | Use alpha channel as mask. |
| `PROMPT` | `1` | Build a mask from `mask_prompt` and `confidence`. |

## API enums

`SeamlessAxes` accepts enum values plus several convenient conversions.

| Name | id | UI text | x | y | Convertible values |
| --- | --- | --- | --- | --- | --- |
| `AUTO` | `auto` | `Auto-detect` | `None` | `None` | `None`, `"auto"`, `"Auto-detect"` |
| `OFF` | `off` | `Off` | `False` | `False` | `False`, `""`, `"off"`, `"Off"`, `(False, False)` |
| `HORIZONTAL` | `x` | `X` | `True` | `False` | `"x"`, `"X"`, `(True, False)` |
| `VERTICAL` | `y` | `Y` | `False` | `True` | `"y"`, `"Y"`, `(False, True)` |
| `BOTH` | `xy` | `Both` | `True` | `True` | `True`, `"xy"`, `"Both"`, `(True, True)` |

Bitwise operators are defined between `SeamlessAxes` values: `&`, `|`, `^`, and `~` combine or invert `x/y` flags.

`StepPreviewMode` values:

- `None`
- `Fast`
- `Fast (Batch Tiled)`
- `Accurate`
- `Accurate (Batch Tiled)`

## Generator enum/dataclass facts used by backends

These types live under `dream_textures.generator_process.models` and are required when a backend calls Dream Textures' Diffusers generator internals.

`Scheduler` display values accepted by `Scheduler(value)`:

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

`ModelType` values and recommendations:

| Name | Value | `recommended_model()` | Primary compatibility fact |
| --- | ---: | --- | --- |
| `UNKNOWN` | `0` | `stabilityai/stable-diffusion-2-1` | Not accepted by `matches_task()` for normal generation. |
| `PROMPT_TO_IMAGE` | `4` | `stabilityai/stable-diffusion-2-1` | Matches `PromptToImage` and `ImageToImage`. |
| `DEPTH` | `5` | `stabilityai/stable-diffusion-2-depth` | Matches `DepthToImage`. |
| `UPSCALING` | `7` | `stabilityai/stable-diffusion-x4-upscaler` | Present in model inference, but this version's `matches_task()` does not accept `Upscale`. |
| `INPAINTING` | `9` | `stabilityai/stable-diffusion-2-inpainting` | Matches `Inpaint` and `Outpaint`. |
| `CONTROL_NET` | `-1` | `stabilityai/stable-diffusion-2-1` | Used as a ControlNet side model, not a main generation model. |
| `UNSPECIFIED_CHECKPOINT` | `-2` | `stabilityai/stable-diffusion-2-1` | Bypasses task matching for linked checkpoints; runtime compatibility is still not guaranteed. |

`Optimizations` verified constructor signature:

```python
Optimizations(
    attention_slicing: bool = True,
    attention_slice_size: str | int = "auto",
    cudnn_benchmark: bool = False,
    tf32: bool = False,
    amp: bool = False,
    half_precision: bool = True,
    cpu_offload: str | CPUOffload = CPUOffload.OFF,
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

`CPUOffload` values are `off`, `model`, and `submodule`. See [Diffusers Backend](diffusers-backend.md) for how scheduler creation, model type validation, and optimization application behave at runtime.

## FixItError facts

`FixItError(message, solution)` is an exception for UI-fixable validation failures. Current solution classes are:

```python
FixItError.ChangeProperty(property: str)
FixItError.RunOperator(title: str, operator: str, modify_operator: Callable[[Any], None])
```

The base backend source docstring shows an `UpdateGenerationArgumentsSolution` example, but that class is not present in the verified API. Use the current solution classes above unless a newer Dream Textures version proves otherwise.

## Image utility facts relevant to backends

`image_utils.ImageOrPath` is a backend-compatible union of NumPy arrays, PIL images, filesystem paths, and Blender images. Common helpers:

- `size(array) -> (width, height)` for `HW`, `HWC`, or `NHWC` arrays.
- `channels(array) -> int` for `HW`, `HWC`, or `NHWC` arrays.
- `image_to_np(image_or_path, dtype=np.float32, mode="RGBA", to_color_space="sRGB", size=None, top_to_bottom=True)` normalizes images for generator actions.
- `np_to_bpy(array, ...)` is Blender-only; do not call it from a non-Blender backend inspection script.
