# Bundled InfiniteYou Runtime

This directory contains the source modules needed by the generated `infinite-you` repo skill to run a complete local InfiniteYou-FLUX generation workflow without depending on the original repository checkout.

## Contents

- `pipelines/pipeline_infu_flux.py` — main `InfUFluxPipeline` wrapper, face embedding, model loading, LoRA loading, and generation call.
- `pipelines/pipeline_flux_infusenet.py` — `FluxInfuseNetPipeline` Diffusers/Flux ControlNet integration.
- `pipelines/resampler.py` — Perceiver-style identity embedding projection module.
- `pipelines/__init__.py` — package marker.
- `requirements.txt` — runtime dependency pins copied from the source snapshot.

## Source and license

These files were copied from the InfiniteYou source snapshot recorded in `../references/repo-provenance.md`. The source files retain their upstream license headers where present. The repository code is Apache License 2.0; model weights, base FLUX weights, InsightFace models, and optional LoRAs have separate licenses and are not bundled here.

## Runtime boundary

The bundled runtime includes code only. It does not include model weights or external support files. Full generation still requires:

- installed Python dependencies from `runtime/requirements.txt`,
- CUDA-capable PyTorch and visible GPU,
- InfiniteYou model files,
- InsightFace support files,
- FLUX base model files or explicitly authorized gated Hugging Face access.

The skill entry points add this `runtime/` directory to `sys.path` automatically. Use an optional source override only when intentionally testing a refreshed checkout.
