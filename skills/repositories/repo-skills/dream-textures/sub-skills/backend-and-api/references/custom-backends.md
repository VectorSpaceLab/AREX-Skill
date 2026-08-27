# Custom Backend Guidance

Use this reference when implementing a Dream Textures backend such as a fake/test backend, a DreamStudio/cloud backend, or an alternate local generator.

## Minimal backend skeleton

```python
bl_info = {
    "name": "My Backend",
    "blender": (3, 1, 0),
    "category": "Paint",
}

import bpy
from dream_textures.api import Backend, Model, GenerationResult
from dream_textures.api.models import PromptToImage, ImageToImage, Inpaint, DepthToImage, Outpaint, Upscale

class MyBackend(Backend):
    name = "My Backend"
    description = "Short UI description"

    # Optional backend-specific UI state.
    # my_option: bpy.props.BoolProperty(name="My Option")

    def list_models(self, context):
        return [Model(name="Example", description="prompt model", id="example-model")]

    def list_controlnet_models(self, context):
        return []

    def list_schedulers(self, context):
        return ["Default"]

    def generate(self, arguments, step_callback, callback):
        try:
            match arguments.task:
                case PromptToImage():
                    pass
                case ImageToImage(image=image, strength=strength, fit=fit):
                    pass
                case Inpaint(image=image, mask_source=mask_source, mask_prompt=mask_prompt, confidence=confidence):
                    pass
                case DepthToImage(depth=depth, image=image, strength=strength):
                    pass
                case Outpaint(image=image, origin=origin):
                    pass
                case Upscale(image=image, tile_size=tile_size, blend=blend):
                    pass
                case _:
                    raise NotImplementedError(type(arguments.task).__name__)

            # Send progress. If this returns False, stop promptly.
            if not step_callback([GenerationResult(progress=0, total=1, seed=arguments.seed, title="Starting")]):
                callback(InterruptedError())
                return

            # Replace with real image data shaped (height, width, 3 or 4).
            callback([GenerationResult(progress=1, total=1, seed=arguments.seed, title="Done", image=None)])
        except Exception as exc:
            callback(exc)

    def validate(self, arguments):
        if arguments.model is None:
            from dream_textures.api.models import FixItError
            raise FixItError("No model selected.", FixItError.ChangeProperty("model"))

def register():
    bpy.utils.register_class(MyBackend)

def unregister():
    bpy.utils.unregister_class(MyBackend)
```

## Current generate signature

The current backend contract is:

```python
def generate(self, arguments: GenerationArguments, step_callback: StepCallback, callback: Callback): ...
```

Do not copy the stale `community_backends/test.py` `generate()` signature from the repository version that takes `task, model, prompt, size, seed, ...` as separate parameters. That community test backend is useful as evidence for add-on registration shape and simple UI properties, but its `generate()` signature must be updated before reuse.

## Required callback behavior

- `step_callback(progress: list[GenerationResult]) -> bool` may be called many times. It returns whether generation should continue.
- When it returns `False`, stop work and call `callback(InterruptedError())`.
- Always call `callback(...)` exactly once for the terminal outcome: either `list[GenerationResult]` or an `Exception`.
- For `arguments.iterations`, final success should contain that many `GenerationResult` objects unless the backend documents a different batching behavior.
- A progress-only result may use `image=None` and a descriptive `title`.
- Final images should be NumPy arrays shaped `(height, width, 3)` or `(height, width, 4)`.

## Model and scheduler IDs

`list_models()` controls the `Model.id` values that come back in `arguments.model.id`. Use stable IDs that your backend can resolve without relying on UI labels.

`list_schedulers()` controls `arguments.scheduler`. A non-Diffusers backend can use any strings it returns. If you call Dream Textures' Diffusers generator internals directly, convert scheduler display values through `Scheduler(value)` or pass enum names to `load_model()` deliberately; do not mix UI display values with low-level enum-name lookup.

## Task matching checklist

Use `match arguments.task` and carry only the fields needed by each task:

- `PromptToImage()`: no image input; respect `arguments.size` or backend defaults.
- `ImageToImage(image, strength, fit)`: `image` is already a NumPy array when created by Dream Textures UI; `fit` means resize to selected size.
- `Inpaint(image, strength, fit, mask_source, mask_prompt, confidence)`: `mask_source` is `Inpaint.MaskSource.ALPHA` or `PROMPT`.
- `DepthToImage(depth, image, strength)`: either depth, image, or both may be provided depending on UI source mode.
- `Outpaint(image, origin)`: origin is relative to the source image's top-left corner.
- `Upscale(image, tile_size, blend)`: used by the upscaling operator; validate explicitly if your backend supports it.

## Validation guidance

`validate(arguments)` runs in the UI path and should be quick: no model downloads, no long inference setup, and no blocking network calls.

Use:

- `ValueError("message")` for non-fixable input errors.
- `FixItError.ChangeProperty("property_name")` to ask the user to change a `DreamPrompt` property.
- `FixItError.RunOperator(title, operator, modify_operator)` to expose a repair operator.

The current `FixItError` implementation does not define `UpdateGenerationArgumentsSolution`; ignore that stale docstring example unless a newer installed API adds it.

## Registration and import constraints

- Backend classes are Blender add-on classes and require `bpy` for real registration.
- Ordinary Python scripts can inspect dataclasses/enums, but should not import UI/runtime backend modules unless they provide a safe `bpy` stub and actor-process guard.
- The Dream Textures add-on directory should normally be importable as `dream_textures` in Blender. If a source checkout has a different directory name, use inspection helpers or install/link it under the importable add-on name rather than changing backend code.
- Keep backend subprocess work picklable if using `Generator`/`Actor`; arguments crossing the actor queues must be picklable.

## When not to implement a backend

Route away from this sub-skill when the user only needs prompt settings, model download/setup, or scene/render workflows. A custom backend is warranted when the generation provider or execution engine changes, not when the user only wants different prompts, schedulers, or model files supported by the existing Diffusers backend.
