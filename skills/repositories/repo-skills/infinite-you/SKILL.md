---
name: infinite-you
description: "Routes InfiniteYou-FLUX identity-preserving photo recrafting tasks
  across self-contained local inference, model/demo setup, and pipeline-internal
  debugging."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# InfiniteYou Repo Skill

Use this skill when a task is about InfiniteYou / InfU / InfiniteYou-FLUX: identity-preserving image generation from a face image, FLUX.1-dev model setup, local Gradio operation, optional LoRA use, CUDA memory reduction, or debugging the custom InfuseNet pipeline.

## Start here

1. Read [references/repo-provenance.md](references/repo-provenance.md) when checking staleness against a current checkout.
2. Read [references/bundled-runtime.md](references/bundled-runtime.md) when you need to know what implementation code is bundled with this skill.
3. Read [references/installation-and-models.md](references/installation-and-models.md) before installing dependencies, resolving model paths, or running generation.
4. Run [scripts/check_infinite_you_environment.py](scripts/check_infinite_you_environment.py) for a safe bundled-runtime/import/CUDA/model-layout preflight that does not download models or run generation.
5. Use the route map below to enter the most specific sub-skill.
6. If the task involves identity images, public demos, model downloads, or generated outputs, check [references/safety-and-licenses.md](references/safety-and-licenses.md).

## Route map

| User task | Read |
| --- | --- |
| Build or debug a local generation command from identity image, prompt, optional control image, LoRA, seed, model version, and memory flags. | [sub-skills/local-inference/SKILL.md](sub-skills/local-inference/SKILL.md) |
| Use the Python `InfUFluxPipeline` API, understand inference parameters, or validate CLI flag names. | [sub-skills/local-inference/SKILL.md](sub-skills/local-inference/SKILL.md) |
| Prepare or validate model directories, Hugging Face access, InsightFace support files, optional LoRAs, or FLUX base model paths. | [sub-skills/demo-and-model-setup/SKILL.md](sub-skills/demo-and-model-setup/SKILL.md) |
| Launch, customize, or troubleshoot the self-contained Gradio demo, model switching, cache behavior, or server binding. | [sub-skills/demo-and-model-setup/SKILL.md](sub-skills/demo-and-model-setup/SKILL.md) |
| Modify/debug face detection, ArcFace embeddings, Resampler projection, InfuseNet ControlNet integration, scheduler guidance, quantization, offload, or adapter internals. | [sub-skills/pipeline-internals/SKILL.md](sub-skills/pipeline-internals/SKILL.md) |
| Diagnose cross-cutting dependency, CUDA, model-access, Gradio, LoRA, or policy failures before choosing a workflow route. | [references/troubleshooting.md](references/troubleshooting.md) |

## Installation baseline

This generated skill bundles the InfiniteYou implementation modules under `runtime/pipelines/`, plus the dependency pins in `runtime/requirements.txt`. In a fresh runtime, create an isolated Python environment, install those pinned dependencies, and run the bundled checker from the skill directory.

```bash
python -m pip install -r runtime/requirements.txt
python scripts/check_infinite_you_environment.py --require-cuda
```

Full generation requires CUDA and external model files/access. The memory-reduction flags `--cpu-offload` and `--quantize-8bit` reduce peak CUDA memory but do not make generation CPU-only. By default, the bundled generation and demo entry points require local model directories; pass `--allow-downloads` only after explicit approval for network/model-license consequences.

## Model and workflow facts

- InfiniteYou-FLUX `v1.0` has two documented variants: `aes_stage2` for default aesthetics/text alignment and `sim_stage1` for higher identity similarity.
- The primary input is an identity image containing a detectable face; an optional control image supplies face keypoints.
- If multiple faces are present, the pipeline selects the largest detected face.
- Optional Realism and Anti-blur LoRAs are examples and are off by default.
- Full local execution needs the FLUX.1-dev base model plus InfiniteYou and InsightFace support files, or explicitly authorized download access.

## Safe operating rules

- Use the bundled runtime and scripts by default; do not require the original checkout for normal generation, demo launch, or signature inspection.
- Run dry-run/preflight helpers before heavy model execution or demo launch.
- Do not download gated or non-commercial-use models, expose a demo server, or process identity images without confirming the user's authorization and policy constraints.
- If source code, dependency pins, model variants, CLI flags, or `pipelines/` APIs changed since the provenance snapshot, refresh this skill and rebuild the bundled runtime before relying on it.

## Useful bundled helpers

- [scripts/check_infinite_you_environment.py](scripts/check_infinite_you_environment.py) — shared bundled-runtime import, CUDA, dependency, and optional model-layout checker.
- [sub-skills/local-inference/scripts/run_infinite_you_flux.py](sub-skills/local-inference/scripts/run_infinite_you_flux.py) — dry-run, preflight, or full local inference wrapper using the bundled runtime.
- [sub-skills/demo-and-model-setup/scripts/check_model_layout.py](sub-skills/demo-and-model-setup/scripts/check_model_layout.py) — model-tree validator with no downloads.
- [sub-skills/demo-and-model-setup/scripts/launch_infinite_you_gradio.py](sub-skills/demo-and-model-setup/scripts/launch_infinite_you_gradio.py) — self-contained Gradio demo launcher using the bundled runtime.
- [sub-skills/pipeline-internals/scripts/inspect_pipeline_signatures.py](sub-skills/pipeline-internals/scripts/inspect_pipeline_signatures.py) — safe signature snapshot for API drift checks against the bundled runtime.
