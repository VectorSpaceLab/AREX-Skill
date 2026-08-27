# Backend/API Troubleshooting

Use this guide for source-level diagnosis without running original repository tests, Blender UI workflows, or model downloads.

## `ModuleNotFoundError: bpy` or import failures outside Blender

Symptoms:

- `import dream_textures` fails in ordinary Python.
- Importing `diffusers_backend.py`, `preferences.py`, operators, or property groups fails because `bpy` is unavailable.
- `api.backend.Backend` is missing after a broad `except` swallowed a failed `bpy` import.

Guidance:

- Real backend class registration must run inside Blender.
- For safe API inspection outside Blender, use `scripts/inspect_public_api.py`; it marks the process as Dream Textures' actor context, sets minimal Blender environment variables, and installs a tiny `bpy` stub only for signature inspection.
- Dataclass-only modules under `api.models` are safer than Blender UI modules, but package root import still needs the actor guard in this repository version.
- `image_utils` outside Blender expects `BLENDER_VERSION` and `BLENDER_OCIO_CONFIG` environment variables unless a safe `bpy` stub is present.

## Actor subprocess and callback lifecycle problems

Symptoms:

- Generation appears to start but final `callback` never runs.
- Cancelling does not stop work.
- An exception from a backend dependency is wrapped as a generic runtime error.

Source facts:

- `Generator` is an `Actor`; the frontend sends method calls to a spawned backend process named `__actor__`.
- The actor backend loads `.python_dependencies` and optional zipped dependencies before running generator actions.
- Actor messages and action arguments must be picklable.
- Generator actions yield a `Future`, add responses as progress arrives, and must call `future.set_done()`.
- `DiffusersBackend` calls `future.cancel()` and `callback(InterruptedError())` when `step_callback` returns `False`.

Checks:

- A custom backend must call terminal `callback(...)` exactly once even on cancellation or exceptions.
- If using `Future` directly, attach response, exception, and done callbacks before consuming the generator.
- If source action code catches `InterruptedError`, confirm it still calls `future.set_done()`; Dream Textures actions do this for prompt/image/inpaint/depth/control paths.
- Inspect `Exception.__cause__` when available; actor wraps traced backend errors in `TracedError` or `RuntimeError(repr(e))` for dependency-origin errors.

## Missing optional backend dependencies

Likely missing packages by symptom:

| Symptom | Likely package/component | Route |
| --- | --- | --- |
| Diffusers pipeline import fails | `diffusers`, `torch`, `accelerate`, `transformers` | `setup-and-models` dependency variant |
| Hugging Face model search/download fails | `huggingface_hub`, `requests`, token/network | `setup-and-models` |
| Prompt-mask inpainting or generated depth loads fail | `transformers` models such as CLIPSeg or DPT | `generation-workflows` for workflow, `setup-and-models` for acquisition |
| ControlNet preprocessor fails | `controlnet_aux` and its transitive dependencies | `generation-workflows` / `scene-integration` depending on source image |
| Image file/color conversion fails | `PIL`, `OpenImageIO`, `PyOpenColorIO`, or Blender color management env | backend/image utility inspection first |
| DirectML path fails | `torch_directml` and Dream Textures DirectML patches | `setup-and-models` Windows DirectML variant |

Do not install all requirement variants at once. Select the platform-specific variant in setup guidance.

## Scheduler key/value errors

Symptoms:

- `ValueError: scheduler expected one of [...]`
- A scheduler display string works in the UI but fails in a direct generator call.

Facts:

- UI/backend contract uses display strings from `DiffusersBackend.list_schedulers()`, e.g. `DPM Solver Multistep`.
- `DiffusersBackend.generate()` converts display strings with `Scheduler(arguments.scheduler)`.
- Low-level `load_model()` fallback string handling uses enum names with `Scheduler[scheduler]`, e.g. `DPM_SOLVER_MULTISTEP`.

Fix:

- In backend code, either pass a `Scheduler` enum or convert UI display strings with `Scheduler(value)` before calling low-level generator utilities.
- When calling `load_model()` directly with a string, pass the enum name, not the UI label.

## Model cache, checkpoint, and config mismatch

Symptoms:

- `model is not a valid repo, imported checkpoint, or path`.
- `does not contain a main or fp16 revision`.
- `Can't find appropriate weights`.
- `Select a depth model, such as 'stabilityai/stable-diffusion-2-depth'`.
- UI says selected model is for the wrong task.

Facts and fixes:

- Hugging Face repo IDs must be present in the local HF cache or downloaded through setup/model management first.
- Diffusers pipeline cache entries need `model_index.json`; individual ControlNet model cache entries need `config.json` and supported weight files.
- Linked `.ckpt`/`.safetensors` files are wrapped as `Checkpoint(path, config)` through `checkpoint_lookup`.
- Wrong `ModelConfig` choice causes wrong pipeline/config loading. Use depth config for `DepthToImage`, inpainting config for `Inpaint`/`Outpaint`, and ControlNet configs for ControlNet weights.
- `ModelType.UNSPECIFIED_CHECKPOINT` bypasses task matching but does not guarantee the checkpoint will run; it only means the UI cannot prove compatibility.
- Upscaling has `ModelType.UPSCALING`, but this version's `ModelType.matches_task()` does not accept `Upscale`; the upscaling operator bypasses normal validation.

## Model/task validation errors

`DiffusersBackend.validate()` uses `model_lookup` and `ModelType.matches_task()`:

- `PromptToImage` and `ImageToImage` require `PROMPT_TO_IMAGE`.
- `DepthToImage` requires `DEPTH`.
- `Inpaint` and `Outpaint` require `INPAINTING`.
- ControlNet models are selected separately from main models.

If no compatible installed model exists, the backend creates a `FixItError` solution to download the recommended model. If a compatible model exists, it asks the user to change the `model` property. Model acquisition details belong in `setup-and-models`.

## Callback/cancellation mistakes in custom backends

Common mistakes:

- Copying the stale community backend `generate()` signature.
- Returning a result instead of calling `callback([...])`.
- Emitting a single `GenerationResult` instead of `list[GenerationResult]`.
- Ignoring `step_callback()` returning `False`.
- Passing PIL/Blender images instead of NumPy arrays in final `GenerationResult.image`.

Corrective pattern:

```python
if not step_callback([GenerationResult(progress=i, total=total, seed=seed, title="Working")]):
    callback(InterruptedError())
    return
callback([GenerationResult(progress=total, total=total, seed=seed, image=image_array)])
```

## DirectML and device-specific surprises

- `choose_device()` checks CUDA before MPS and DirectML; set `cpu_only=True` for a deliberate CPU path.
- DirectML requires `torch_directml`; Dream Textures renames PyTorch privateuse1 backend to `dml` and toggles directml patches in `Optimizations.apply()`.
- MPS and DirectML use CPU `torch.Generator` objects because those devices do not support the generator API used here.
- Some schedulers are known in source comments to be non-functional on MPS, notably `KDPM2 Discrete`.

## Source inspection sanity checks

Run the bundled helper before making API claims:

```bash
python scripts/inspect_public_api.py --help
python scripts/inspect_public_api.py --addon-dir /path/to/dream_textures --json
```

Expected signal includes `GenerationArguments`, task dataclass signatures, `SeamlessAxes`, `StepPreviewMode`, Diffusers `Scheduler` values, `ModelType` values, and a tiny `image_utils` array smoke. When inspecting a source directory whose folder is not named `dream_textures`, printed signatures may show that source folder basename as the Python package name; API shape is still the relevant signal. The helper does not validate full Blender UI registration or image generation.
