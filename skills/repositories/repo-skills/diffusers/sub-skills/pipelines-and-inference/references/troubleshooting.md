# Pipeline Troubleshooting

Use this reference to diagnose Diffusers pipeline inference failures. It covers branch-owned runtime failures: imports, optional dependencies, backend/device/dtype choices, local/offline files, API misuse, inpainting/control input issues, callbacks, batching, and serving concurrency.

## Fast Triage

1. Confirm imports and versions with `python scripts/pipeline_env_check.py`.
2. Confirm the model source policy: local/offline snapshot vs. allowed download.
3. Inspect device and dtype together: CPU means float32; CUDA can use fp16/bf16; MPS may need conservative dtype and attention slicing.
4. Check the concrete pipeline `__call__` signature before passing workflow-specific names such as `image`, `mask_image`, `control_image`, `strength`, or `callback_on_step_end_tensor_inputs`.
5. Reproduce with `num_inference_steps=1`, a tiny batch, and a fresh CPU generator.

## Install and Optional Dependency Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'diffusers'` | Package not installed in the active interpreter | Install the package/environment the user intends to run, then verify with the env check script. |
| `ImportError` for `transformers`, `accelerate`, `safetensors`, `PIL`, `cv2`, `fastapi`, or `aiohttp` | Optional dependency required by the chosen pipeline, loading mode, image preprocessing, or server | Install only the missing dependency needed for the selected workflow. |
| `device_map` errors | Accelerate missing or unsupported placement target | Install/enable Accelerate or use `.to(device)` placement instead. |
| xFormers/FlashAttention/backend import error | Optional attention backend unavailable or incompatible with torch/GPU | Remove the backend optimization unless the user explicitly requested it and hardware supports it. |
| Tokenizer/text encoder import error | Text pipelines need Transformers components | Install compatible Transformers or choose a local snapshot with all components present. |

## Device and Dtype Mistakes

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| fp16 operation fails on CPU | `torch_dtype=torch.float16` with CPU execution | Use `torch.float32` on CPU or move to CUDA before fp16 inference. |
| CUDA tensor/device mismatch | Inputs, generators, or model components on incompatible devices | Keep PIL inputs as PIL when supported; for tensors, move them to the pipeline device and dtype. Use CPU generators for reproducibility unless the pipeline requires device-specific generators. |
| Out of memory | Batch/resolution/model too large | Reduce batch size/resolution/steps, enable model CPU offload, use attention/vae slicing, or use `device_map="auto"`. |
| `hf_device_map` exists but `.to("cuda")` fails or wastes memory | Device-map-loaded pipeline moved after Accelerate placement | Do not call `.to()` on a device-mapped pipeline unless deliberately resetting placement. |
| MPS run is slow or unstable | Unsupported dtype/op or memory pressure | Use conservative dtype, call `.to("mps")`, try `enable_attention_slicing()`, and run a small warmup. |

## Local, Offline, and Hub File Problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `local_files_only=True` cannot find files | Local snapshot missing required component files | Point to a complete local model directory or allow a one-time download outside offline mode. |
| 401/403 or gated model error | Private/gated model without accepted terms or token | Have the user authenticate and accept terms before downloading; do not embed tokens in code. |
| `variant="fp16"` not found | The repo/local snapshot lacks variant files | Remove `variant`, use the available variant, or fetch the correct snapshot. |
| safetensors error | `use_safetensors=True` but files are absent/incomplete | Use a snapshot with safetensors or remove the flag if the source is trusted and another format is required. |
| Config/component missing | Partial local copy | Use a full `snapshot_download` result or a complete `save_pretrained` directory. |

## API Misuse

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `unexpected keyword argument 'control_image'` | Concrete pipeline expects `image` or another name | Inspect the pipeline signature and use the model-family-specific input name. |
| `unexpected keyword argument 'callback_on_step_end_tensor_inputs'` | Pipeline does not support new callback API | Remove callback arguments or use the callback API supported by that pipeline version. |
| Empty or wrong output access | Treating output as a PIL image directly | Access `result.images[0]`, or use `return_dict=False` and read tuple element 0. |
| Different result on repeated calls with same generator | Reused generator state advanced | Recreate/reseed a fresh generator for each deterministic call. |
| Batched outputs mismatch expected count | `num_images_per_prompt` multiplies each prompt, or list fields do not match | Expected count is `len(prompts) * num_images_per_prompt`; align list-valued inputs. |

## Inpainting Diagnostic Case

When a user mixes image/mask sizes, CPU fp16, and a missing model token, resolve in this order:

1. Authentication/locality: if model is gated/private and downloads are allowed, ask the user to authenticate outside the code path; if offline, require a complete local snapshot and set `local_files_only=True`.
2. Dtype/device: if `torch.cuda.is_available()` is false, remove `torch.float16` and use float32 CPU execution.
3. Input geometry: load both `image` and `mask_image`, convert to RGB or the pipeline-supported mode, and assert `image.size == mask_image.size` before calling the pipeline.
4. Dimensions: pass `height=image.height` and `width=image.width` only if supported and compatible with the model's scale factor; otherwise resize/crop both image and mask together.
5. Reproduce with `num_inference_steps=1` and a fresh CPU generator.

Minimal guard:

```python
if image.size != mask_image.size:
    raise ValueError(f"image and mask_image must have the same size, got {image.size} and {mask_image.size}")
if device == "cpu" and dtype is torch.float16:
    raise ValueError("Do not run Diffusers pipelines in float16 on CPU; use float32 or a CUDA device")
```

## Control Workflow Errors

- For classic Stable Diffusion ControlNet, conditioning image is often `image`.
- For SD3/Flux ControlNet variants, conditioning image may be `control_image`.
- Multi-control calls require parallel lists for images and `controlnet_conditioning_scale` values when using multiple controls.
- Preprocessing such as Canny/depth/pose must produce an image or tensor with shape and channels expected by the selected control model.
- `guess_mode`, conditioning scales, and start/end guidance windows are pipeline-specific; do not pass them generically without checking support.

## Callback Errors

- Callback function signature should be `(pipe, step_index, timestep, callback_kwargs)` for `callback_on_step_end`.
- Return `callback_kwargs`; do not return `None` unless the concrete API says it is allowed.
- `callback_on_step_end_tensor_inputs` must list supported tensor names. Use the pipeline's `_callback_tensor_inputs` if inspecting interactively.
- Heavy per-step decoding can dominate runtime or exhaust memory; save only selected steps for production.
- Early stopping uses `pipe._interrupt = True` in callback-style examples; avoid mutating other private attributes unless the task explicitly requires it.

## Serving and Concurrency Errors

| Symptom | Cause | Fix |
| --- | --- | --- |
| Intermittent scheduler index errors under concurrent requests | Shared mutable scheduler state | Clone scheduler from config and create a per-request pipeline via `from_pipe`. |
| GPU memory grows per request | Loading model inside handler or keeping request pipelines alive | Load once at startup and release per-request references. |
| Identical outputs across unrelated requests | Reusing one generator object | Create one generator per request and seed deliberately. |
| Event loop blocked | Running pipeline call directly in async handler | Use an executor/thread worker for the blocking pipeline call. |
| Unsafe user inputs | Missing prompt/size/batch validation | Validate prompt type/length, image dimensions, requested count, seed bounds, and local/download policy before inference. |

## Safe Offline Skeleton Checklist

A robust offline pipeline skeleton should include:

- Local path existence check.
- `local_files_only=True` in every `from_pretrained` call.
- CPU/GPU fallback with dtype tied to device.
- Fresh CPU generator seeded from a validated integer.
- Optional `callback_on_step_end` only if the concrete pipeline supports it.
- Explicit no-download default, with download allowed only by a user-controlled flag.
