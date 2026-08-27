# Bundled Runtime Implementation

## Purpose

Read this when you need to understand why the generated skill can run InfiniteYou-FLUX without the original repository checkout. The skill bundles the implementation code needed by local inference, Gradio launch, and signature inspection entry points.

## Bundled files

| Runtime file | Role |
| --- | --- |
| `runtime/pipelines/pipeline_infu_flux.py` | Main `InfUFluxPipeline`, face detection/embedding, model loading, LoRA loading, and image generation call. |
| `runtime/pipelines/pipeline_flux_infusenet.py` | Diffusers `FluxControlNetPipeline` subclass with InfuseNet residual/control guidance behavior. |
| `runtime/pipelines/resampler.py` | Perceiver-style identity embedding projection module. |
| `runtime/pipelines/__init__.py` | Package marker for the bundled `pipelines` package. |
| `runtime/requirements.txt` | Dependency pins copied from the source snapshot. |

The bundled entry points add `runtime/` to `sys.path` automatically and import `pipelines.*` from there. No command in this generated skill needs the original checkout for normal operation.

## What is not bundled

The runtime code is self-contained, but model artifacts are not included:

- InfiniteYou `infu_flux_v1.0/<variant>/InfuseNetModel` directories.
- InfiniteYou `image_proj_model.bin` files.
- `supports/insightface` support files.
- Optional LoRA safetensors.
- FLUX.1-dev base model files.

Use the model-layout checker before full generation. Pass `--allow-downloads` to generation or demo entry points only when the user explicitly accepts network/model-license consequences.

## Override policy

Most users should omit implementation override flags. The optional `--implementation-root` / `--repo-root` compatibility alias exists for refresh/debug scenarios where a different checkout must be compared against this bundled snapshot. If using an override, re-run signature and helper checks because the generated references may become stale.
