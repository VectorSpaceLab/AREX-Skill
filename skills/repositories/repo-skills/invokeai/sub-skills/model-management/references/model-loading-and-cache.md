# Model Loading and Cache

InvokeAI loading is a separate layer from model records and installation. Records describe models; loaders instantiate them; the cache mediates RAM and execution-device memory.

## Load Service

The model load service takes a validated model config and optional submodel type, then:

1. Emits model-load start events when running inside the app.
2. Selects a loader implementation by config `base`, `type`, `format`, and optional submodel type.
3. Loads the model through that implementation.
4. Stores the loaded object in the RAM cache.
5. Returns a `LoadedModel` context manager that locks/unlocks cache entries and moves models to the execution device only while in use.

For ad-hoc model files, `load_model_from_path()` can load safetensors, torch pickle-style checkpoints, or diffusers directories into the RAM cache. Treat this as a loading operation, not a metadata diagnostic; pickle-style files invoke malware scanning and may still be risky.

## Loaded Model Context

A loaded model can be used in two styles:

- Direct context manager: locks the model, moves it onto the execution device when appropriate, and returns the runtime model.
- `model_on_device()` context: returns a tuple of optional CPU state dict plus model on device. The CPU state dict is intended as read-only restoration support for patchers such as LoRA.

If partial loading is active, `repair_required_tensors_on_device()` ensures required tensors are resident before use.

## Cache Model

The model cache has two storage levels:

| Layer | Purpose |
| --- | --- |
| Storage device | Usually CPU RAM. Keeps cached copies and uses least-recently-used eviction. |
| Execution device | Usually CUDA, MPS, or CPU. Keeps active models and uses smallest-first offload for unlocked entries. |

The cache wraps public operations in locks. It may keep a RAM copy of weights, partially load large CUDA models, and clear unlocked models after a configured keep-alive timeout.

## RAM and VRAM Behavior

- RAM cache size can be configured directly; otherwise it is derived from system memory, CUDA VRAM, and a minimum floor.
- VRAM cache size can be configured directly; otherwise available execution-device memory minus working memory is used.
- `make_room()` evicts unlocked RAM cache entries by least-recently-used order.
- `lock()` moves as much of the target model as possible to the execution device, offloading unlocked models first.
- Locked models are not offloaded to make room for other models; this matters when invocation code loads models in a suboptimal order.
- On CUDA, partial loading can move only part of a module to VRAM; on CPU and MPS, full-load behavior is used instead.
- Out-of-memory during movement deletes the problematic cache entry and re-raises the error.

## CPU-Only and FP8 Settings

- Main model default settings can mark text encoders as `cpu_only`; standalone T5/Qwen/TextLLM configs can also carry `cpu_only`.
- CPU-only logic applies to text encoder submodels or standalone encoder configs, preserving GPU memory for denoisers.
- FP8 layerwise casting is CUDA-only and disabled for Z-Image, VAEs, LoRAs, ControlLoRAs, text encoders, tokenizers, schedulers, safety checkers, and VAE submodels.
- FP8 applies only when supported default settings request it. Precision-sensitive module names such as norms and projection in/out layers are skipped.

## Picklescan and Weight Loading Safety

- Safetensors metadata and tensor headers are safe diagnostic targets.
- `.ckpt`, `.pt`, `.pth`, and `.bin` files are pickle-style or may contain pickle content. Loading them should be avoided for diagnostics unless the user accepts risk.
- Pickle-based loads are scanned first. If scan detects infection or scan errors, loading aborts unless the unsafe picklescan-disable setting is active.
- Do not recommend disabling picklescan as a routine fix. If it is already disabled, document the increased risk.

## Cache Diagnostics Without Generation

Prefer this order:

1. Inspect model record fields: `key`, `name`, `base`, `type`, `format`, `variant`, `path`, `hash`, and default settings.
2. Check whether the resolved file/directory exists and whether the record is external.
3. Check cache stats or cache-entry logs if the app exposes them.
4. Inspect config settings controlling model path, RAM/VRAM cache limits, execution device, partial loading, keep RAM copy, and keep-alive timeout through the operations-config sub-skill.
5. Avoid a full generation run. If a true load test is needed, ask for explicit permission and keep it bounded to one known model or submodel.

## Common Load Failure Causes

- Missing or moved files referenced by a stale record path.
- Wrong `base`, `type`, `format`, or `variant` causing no loader implementation or an incompatible loader.
- Optional dependencies missing for diffusers, transformers, bitsandbytes, GGUF, ONNX, or provider code paths.
- CUDA/ROCm/MPS/CPU mismatch, unsupported dtype, insufficient VRAM, or cache limit too small.
- CPU-only or FP8 settings applied to a model where the user expected GPU/full-precision behavior.
- LoRA or ControlLoRA patch loaded as a standalone model rather than attached to a compatible base model.