# LTX-2 Package Map

## When to read

Read this when deciding which LTX-2 package or sub-skill owns a task, or when translating user wording into package imports, scripts, and model assets.

## Package roles

| Distribution | Import roots | Primary role | Routes |
| --- | --- | --- | --- |
| `ltx-core` | `ltx_core` | Core model definitions, diffusion components, conditioning, loaders, state-dict operations, VAEs, text encoders, block streaming, quantization policy objects, HDR/color helpers. | Use `core-components` for APIs; `performance-backends` for backend-specific paths. |
| `ltx-pipelines` | `ltx_pipelines` | High-level generation pipelines and CLIs for text/image/video/audio generation, retake, HDR/EXR, Dub-It, DFR, and multi-GPU inference wrappers. | Use `inference-pipelines`; use `performance-backends` for optimization/multi-GPU. |
| `ltx-trainer` | `ltx_trainer` | Training/fine-tuning config schema, flexible strategy, trainer loop, datasets, model loading, validation, checkpointing, and training utilities. | Use `training-workflows` and `data-preparation`. |
| `ltx-kernels` | `ltx_kernels` | Optional CUDA/C++ kernels for all-to-all, blockwise FP8/FP6, NVFP4, and VAE CuTe DSL acceleration. | Use `performance-backends`; do not assume it is installed. |

## Installation patterns

The public repository is a monorepo. A source checkout normally uses `uv` workspace commands such as:

```bash
uv sync
```

For inference with the diffusion VAE neighborhood-attention extra, the repository documents an optional `natten` extra on `ltx-core`. For compiled kernels, it documents an opt-in `kernels` dependency group. These optional paths are backend-specific; read `performance-backends` before installing them.

For package inspection or scripts that only import the packages, verify imports first:

```bash
python - <<'PY'
import ltx_core, ltx_pipelines, ltx_trainer
print('ltx packages import')
PY
```

`ltx-kernels` is optional and may fail to import unless compiled for the host.

## Task-to-sub-skill map

| Task language | Primary owner | Notes |
| --- | --- | --- |
| "generate a video", "which pipeline", "DistilledPipeline", "retake", "Dub-It", "HDR", "EXR", "audio-to-video" | `inference-pipelines` | Also read `model-assets.md` for required checkpoint files. |
| "prepare data", "caption videos", "preprocess latents", "dataset JSON", "resolution buckets", "reference video", "mask" | `data-preparation` | Actual preprocessing is heavy; bundled helpers validate and build commands first. |
| "train a LoRA", "fine-tune", "I2V/T2V/V2A", "config YAML", "resume", "W&B", "Hub" | `training-workflows` | Route raw media and `.precomputed/` validation back to `data-preparation`. |
| "custom pipeline code", "SingleGPUModelBuilder", "ModelPaths", "SDOps", "scheduler", "guider", "VAE shape" | `core-components` | Use package APIs and avoid loading checkpoints unless user supplies local files. |
| "OOM", "FP8", "offload", "natten", "ltx-kernels", "NVFP4", "multi-GPU", "torch.compile" | `performance-backends` | Separate verified CUDA readiness from optional accelerators. |

## Public entry point reminders

- Pipeline CLIs are Python modules under `ltx_pipelines`, such as `ltx_pipelines.distilled` and `ltx_pipelines.ti2vid_two_stages`.
- Trainer configs are validated by `ltx_trainer.config.LtxTrainerConfig`.
- Core code uses `ltx_pipelines.utils.model_paths.ModelPaths` to normalize monolith versus split checkpoint layouts.
- Bundled skill scripts are intentionally safe by default and either inspect, validate, or print commands; they do not download models, train, or generate media unless a future user explicitly runs a launcher designed for that purpose.
