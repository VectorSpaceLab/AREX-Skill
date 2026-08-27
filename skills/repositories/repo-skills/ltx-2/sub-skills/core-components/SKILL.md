---
name: core-components
description: "Helps agents build custom LTX-2 core component code with ltx_core
  APIs, model loaders, diffusion schedulers/guiders, conditioning, LoRA,
  quantization, media, and shape troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Core Components

Use this sub-skill when a user wants custom Python code against LTX-2 internals rather than a ready-made command line pipeline. It covers `ltx_core` building blocks and the package utilities that wire them together: model path contracts, model builders, state-dict operations, schedulers, guiders, noisers, patchifiers, conditioning items, generated keyframe slots, LoRA fusion, quantization policies, text/audio/video component classes, and safe media/HDR helpers.

## Route here for

- Writing or reviewing custom denoising loops, diffusion stages, model builders, or component wiring.
- Inspecting exact class/function names and import paths for `ltx_core` and relevant `ltx_pipelines.utils` modules.
- Debugging wrong API names such as `LinearQuadraticSchedule` instead of `LinearQuadraticScheduler`, or `ClassifierFreeGuidance` instead of `CFGGuider`.
- Explaining latent/video/audio/text tensor shapes, frame alignment, VAE scale factors, patchification, `Modality`, and `LatentState` layouts.
- Using `ModelPaths`, `SingleGPUModelBuilder`, `SDOps`, LoRA maps, `QuantizationPolicy`, FP8 policy factories, or block streaming builders without loading real checkpoints in examples.
- Diagnosing generated keyframe slot errors and checkpoint requirements.

## Route elsewhere

- Complete runnable inference recipes, CLI flags, output writing, prompt/HDR pipeline workflows, or model asset selection: read `../inference-pipelines/SKILL.md`.
- Dataset preparation, captioning, manifests, preprocessing, references, masks, and precomputed latents for training: read `../data-preparation/SKILL.md`.
- Training/fine-tuning configs, launch/resume, validation, optimizer, W&B, or custom strategies: read `../training-workflows/SKILL.md`.
- CUDA installation, optional kernels, NATTEN/FlashAttention, NVFP4 hardware, multi-GPU, compile/offload performance tuning: read `../performance-backends/SKILL.md`.

## Read first

- [API reference](references/api-reference.md) for verified imports, exact signatures, and selected pipeline constructor surfaces.
- [Model and data shapes](references/model-and-data-shapes.md) for latent layouts, patchification, frame/spatial alignment, text/audio context shapes, and generated keyframe slot constraints.
- [Loading and LoRAs](references/loading-and-loras.md) for `ModelPaths`, `SingleGPUModelBuilder`, `SDOps`, safetensors metadata, LoRA fusion, block streaming, and quantization policy wiring.
- [Troubleshooting](references/troubleshooting.md) for wrong names, missing component paths, shape errors, LoRA metadata/key mismatches, keyframe-capable checkpoint requirements, and optional backend routing.

## Safe helper

Run the bundled inspector in any Python environment where LTX-2 packages are installed. It performs imports, signature inspection, and optional tiny CPU shape checks only; it does not download models or load checkpoints.

```bash
python sub-skills/core-components/scripts/inspect_core_api.py --help
python sub-skills/core-components/scripts/inspect_core_api.py --json --tiny-shapes
python sub-skills/core-components/scripts/inspect_core_api.py --include-pipelines --object ltx_pipelines.distilled:DistilledPipeline
```

## Core coding rules

1. Treat docs and examples as conceptual only unless the exact import and signature appear in [API reference](references/api-reference.md) or are re-inspected with the helper.
2. Use placeholders for checkpoint paths in examples and state clearly when real `.safetensors` files are required. Do not write examples that silently load missing model assets.
3. Build path contracts with `ModelPaths.from_monolith(...)` or `ModelPaths.from_split(...)`; do not mix monolith checkpoint/Gemma flags with split component flags.
4. For LoRA loading, pair each adapter with a matching `SDOps` map and a strength; preserve CPU LoRA staging unless the user explicitly accepts higher GPU memory use.
5. For FP8, create a `QuantizationPolicy` first and pass its `sd_ops`, `module_ops`, and `fuse_rule` into the builder. Route NVFP4 and compiled-kernel constraints to `performance-backends`.
6. For generated keyframe slots, require a checkpoint whose transformer config sets `use_keyframes_abs_pos_embedding`; otherwise recommend DFR/generated-keyframe-capable assets or route to the inference pipeline owner.
