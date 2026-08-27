---
name: inference-api
description: "Use the installed sgm.inference.api Python API for SDXL
  text-to-image, image-to-image, refiner handoff, sampler choices, model specs,
  and safe API inspection."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Inference API

Use this sub-skill when a task asks for the installed `sgm.inference.api` Python API: constructing `SamplingPipeline`, choosing SDXL base/refiner architectures, selecting samplers/discretizations/guiders, using `SamplingParams`, returning latents, running `image_to_image` with strength, or inspecting the API safely without loading checkpoints.

## Route Here For

- `SamplingPipeline` construction and the default `model_path="checkpoints"`, `config_path="configs/inference"`, `device="cuda"`, `use_fp16=True` behavior.
- SDXL text-to-image, image-to-image, and base-to-refiner plans that use `SamplingParams` and `return_latents=True`.
- API-level sampler selection among `EulerEDMSampler`, `HeunEDMSampler`, `EulerAncestralSampler`, `DPMPP2SAncestralSampler`, `DPMPP2MSampler`, and `LinearMultistepSampler`.
- Diagnosing checkpoint/config mismatches, CPU-only environments, invalid enum strings, `img2img_strength`, image tensor shape, and missing optional dependencies.

## Start With

- Read [references/api-reference.md](references/api-reference.md) for exact signatures, enum values, `SamplingParams` defaults, model specs, and helper behavior.
- Read [references/workflows.md](references/workflows.md) for SDXL txt2img, img2img, base+refiner, dry-run inspection, and validation patterns.
- Read [references/troubleshooting.md](references/troubleshooting.md) when a pipeline fails to initialize, sample, load a checkpoint, or run in CPU-only conditions.
- Run `python scripts/inspect_inference_api.py --json --assert-expected` from this sub-skill directory, or call the script by path from any cwd, to inspect importable API facts without loading configs or checkpoints.

## Boundaries And Cross-Links

- Use the root [generative-models skill](../../SKILL.md) for repository-level routing and package context.
- Route standalone SVD, SV3D, SV4D, and video sampling scripts to [video-sampling](../video-sampling/SKILL.md).
- Route training configuration authoring and training YAML design to [training-and-configs](../training-and-configs/SKILL.md).
- Route UI demos, Streamlit surfaces, and watermark detection workflows to [demos-and-watermarking](../demos-and-watermarking/SKILL.md).
- Keep this sub-skill focused on the installed SDXL inference API and its helpers; do not require future agents to reopen source repository files.
