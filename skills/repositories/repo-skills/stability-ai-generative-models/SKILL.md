---
name: stability-ai-generative-models
description: "Use Stability AI's generative-models package for SDXL inference
  APIs, SVD/SV3D/SV4D video sampling, config-driven training, demos, and
  watermarking workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Generative Models

Use this repo skill when a task involves Stability AI `generative-models`, the installed `sgm` package, SDXL inference APIs, Stable Video Diffusion or SV3D/SV4D sampling scripts, config-driven diffusion training, demo apps, or invisible watermark detection.

## Route By Task

- Use [inference-api](sub-skills/inference-api/SKILL.md) for `sgm.inference.api`, `SamplingPipeline`, SDXL text-to-image/image-to-image, base+refiner latent handoff, sampler choices, and checkpoint/config mismatch diagnosis.
- Use [video-sampling](sub-skills/video-sampling/SKILL.md) for standalone SVD, SVD-XT, SV3D, SV4D, SV4D2, 8-view video-to-4D, camera-path, input video/frame, and low-VRAM sampling workflows.
- Use [training-and-configs](sub-skills/training-and-configs/SKILL.md) for `main.py --base`, OmegaConf dotlist overrides, `instantiate_from_config`, `DiffusionEngine`, `AutoencodingEngine`, toy/example training configs, and static config validation.
- Use [demos-and-watermarking](sub-skills/demos-and-watermarking/SKILL.md) for Streamlit/Gradio demo routing, SDXL Turbo demo behavior, converting demo controls into automated calls, and watermark bit-match interpretation.

## Install And Import Context

- The Python distribution is `sgm`; the public import is `sgm`; the repository snapshot used for this skill reports version `0.1.0`.
- The package metadata does not declare the full runtime dependency set. For real sampling/training, install a PyTorch-compatible environment plus the documented runtime requirements for the selected workflow.
- For static inspection or planning, use the minimal import check below before attempting checkpoint-backed execution.

```bash
python -c "import sgm; print(sgm.__version__)"
python scripts/check_environment.py --json
```

## Working Safely

- Do not load checkpoints, start UI servers, download model weights, or launch training until the user confirms runtime cost, credentials, GPU availability, and output paths.
- Treat CUDA/GPU, checkpoint files, Hugging Face access, `xformers`, `rembg`, Streamlit/Gradio, and video encoders as workflow-specific prerequisites rather than assumptions.
- Prefer bundled helper scripts for safe inspection: they avoid checkpoint loads and long-running execution.
- Read [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting install/import, optional dependency, checkpoint, CUDA, and data/config failures.
- Read [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill matches a current checkout or should be refreshed.

## Bundled Helpers

- `scripts/check_environment.py` checks required imports, optional dependency visibility, distribution versions, and torch/CUDA facts without loading checkpoints.
- `sub-skills/inference-api/scripts/inspect_inference_api.py` inspects API signatures, enum values, and model specs.
- `sub-skills/video-sampling/scripts/inspect_video_sampling_cli.py` statically summarizes video sampling script defaults, configs, checkpoints, inputs, and command templates.
- `sub-skills/training-and-configs/scripts/inspect_training_config.py` validates and summarizes training config files without starting training.
- `sub-skills/demos-and-watermarking/scripts/watermark_match_thresholds.py` classifies watermark bit-match counts without image-processing dependencies.

## Common Non-Fits

- Use a Diffusers-specific skill for Hugging Face Diffusers pipeline APIs that do not involve `sgm` or this repository's scripts.
- Use a generic PyTorch Lightning skill for framework-only trainer questions without `generative-models` configs or classes.
- Use a computer-vision/model-serving skill when the request is about deployment frameworks rather than this package's generation, demo, or training surfaces.
