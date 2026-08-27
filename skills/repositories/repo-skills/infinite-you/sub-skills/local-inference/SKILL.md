---
name: local-inference
description: "Routes InfiniteYou-FLUX self-contained identity-preserving image
  generation through the bundled runtime helper, model variants, control images,
  LoRA options, and CUDA memory settings."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Local Inference

Use this sub-skill when a task asks how to run, adapt, debug, or validate local InfiniteYou-FLUX image generation from an identity image and text prompt. The bundled helper uses this skill's `runtime/pipelines/` implementation by default, so normal generation does not require the original repository checkout.

## Read first

- [references/workflows.md](references/workflows.md) for common identity, control-image, model-variant, LoRA, and low-memory recipes.
- [references/cli-reference.md](references/cli-reference.md) for the generated helper flags and the official CLI surface it mirrors.
- [references/api-reference.md](references/api-reference.md) for verified `InfUFluxPipeline` signatures and parameter semantics.
- [references/troubleshooting.md](references/troubleshooting.md) for face, CUDA, model-access, LoRA, prompt, and output failures.
- [scripts/run_infinite_you_flux.py](scripts/run_infinite_you_flux.py) when you need a bundled dry-run, preflight, or generation entry point.

## Use this route for

- Building a local generation command from an identity image, prompt, optional control image, seed, size, and output directory.
- Choosing between `aes_stage2` and `sim_stage1` model variants.
- Deciding whether to enable `--cpu-offload`, `--quantize-8bit`, or both to reduce peak VRAM.
- Using optional Realism or Anti-blur LoRA files when the local model tree contains them.
- Calling the bundled Python API directly through `InfUFluxPipeline`.
- Preflighting images, bundled runtime imports, CUDA availability, and local model paths before a heavy run.

## Fast workflow

1. Check setup and model access in the root [installation and models reference](../../references/installation-and-models.md). Full generation requires CUDA and model files/access; `--cpu-offload` is not CPU-only execution.
2. Run a no-side-effect plan first:
   ```bash
   python scripts/run_infinite_you_flux.py --dry-run \
     --id-image path/to/id.jpg \
     --prompt "A person, portrait, cinematic" \
     --model-dir models/InfiniteYou \
     --base-model-path models/FLUX.1-dev \
     --cpu-offload --quantize-8bit
   ```
3. Run a preflight check before generation:
   ```bash
   python scripts/run_infinite_you_flux.py --check-only \
     --id-image path/to/id.jpg \
     --prompt "A person, portrait, cinematic" \
     --model-dir models/InfiniteYou \
     --base-model-path models/FLUX.1-dev
   ```
4. If preflight passes and CUDA/model access is available, run without `--dry-run` or `--check-only`.
5. Confirm a PNG was written and record the seed from the output filename or terminal output.

## Route elsewhere

- For model directory layout, Hugging Face access, demo model switching, or Gradio launch questions, read [../demo-and-model-setup/SKILL.md](../demo-and-model-setup/SKILL.md).
- For modifying face detection, Resampler, InfuseNet injection, offload internals, or Diffusers integration, read [../pipeline-internals/SKILL.md](../pipeline-internals/SKILL.md).
- For code/model license and responsible-use constraints, read [../../references/safety-and-licenses.md](../../references/safety-and-licenses.md).

## Acceptance checks

A good local-inference answer should name the exact generation inputs, model variant, CUDA/memory strategy, model path/access assumptions, whether downloads are allowed, and validation signal. It should avoid telling the user to open or run source-repo scripts directly; use the bundled helper or describe an equivalent API call against the bundled runtime.
