---
name: mimicmotion
description: "Routes MimicMotion's CUDA-first local inference and Cog deployment
  workflows, including runtime preflight checks, sample-config generation, and
  MP4 output."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# MimicMotion

MimicMotion generates human-motion videos from a reference image and a motion video. Use this skill when the task mentions MimicMotion, Stable Video Diffusion, DWPose, a sample config, checkpoint switching, or MP4 generation.

## Start here

1. Read `references/environment.md` if the environment is not already known to be CUDA-ready.
2. Read `references/configuration.md` for the required weights layout and the canonical sample config.
3. Read `references/workflows.md` to choose between local inference and Cog deployment.
4. Read `references/troubleshooting.md` if imports, weights, CUDA, or video writing fail.
5. Read `references/repo-provenance.md` when checking whether this skill matches the current checkout.

## Install the runtime

Use a Python 3.11 CUDA environment. The verified stack was:

- `torch==2.5.1+cu124`
- `torchvision==0.20.1+cu124`
- `diffusers==0.27.0`
- `transformers==4.32.1`
- `huggingface-hub==0.20.2`
- `decord==0.6.0`
- `onnxruntime-gpu==1.29.0`
- `einops==0.8.0`
- `omegaconf==2.3.0`
- `opencv-python==4.10.0.84`
- `matplotlib==3.9.1`
- `av==12.2.0`
- `cog==0.22.0` when using the deployment path
- `ffmpeg` available on PATH

If `diffusers` import errors mention `cached_download`, pin `huggingface-hub==0.20.2`. If `decord` is only available as a failing PyPI wheel on your platform, use the conda-forge build documented in `references/environment.md`.

## Main workflows

| Workflow | When to use | Read / run |
| --- | --- | --- |
| Local inference | You have a MimicMotion checkout, the CUDA stack is ready, and you want to generate a video from the sample config or a custom config. | Read `references/workflows.md`, then run `scripts/check_runtime.py` and `scripts/run_inference.py`. |
| Cog deployment | You want to understand the packaged predictor surface, input validation, or weight-fetch behavior. | Read `references/workflows.md` and `references/configuration.md`. |
| Runtime preflight | You want to confirm imports, CUDA providers, `ffmpeg`, and the local package surface before generating a video. | Run `scripts/check_runtime.py --repo-root <checkout>`. |

## Scripts

- `scripts/check_runtime.py` — run this first. It checks the imported package stack, CUDA availability, ONNXRuntime CUDA providers, `ffmpeg`, and optionally the local model files.
- `scripts/run_inference.py` — run this after preflight when you want the bundled local-inference wrapper that mirrors the repository CLI.

## What to expect from the model

- The default sample config uses `assets/example_data/videos/pose1.mp4` and `assets/example_data/images/demo1.jpg`.
- The canonical checkpoint is `models/MimicMotion_1-1.pth`.
- The local inference flow writes one MP4 per test case.
- The Cog predictor supports checkpoint switching between `v1` and `v1-1` and validates numeric bounds before generation.

## Safety and capability notes

- Treat CUDA as required for the main workflow. A CPU-only environment is not a verified substitute for MimicMotion generation.
- Use `scripts/check_runtime.py --skip-models` only when you need to confirm the Python/CUDA stack before the weights are available.
- Do not assume the environment is ready just because imports succeed; the pipeline also needs the model files and `ffmpeg`.

## Related references

- `references/api-reference.md` for verified signatures and output behavior.
- `references/environment.md` for the installation shape and backend checks.
- `references/configuration.md` for weights, config, and asset layout.
- `references/troubleshooting.md` for predictable import, backend, and video-writing failures.
- `references/repo-routing-metadata.json` for managed skill routing metadata.
- `references/repo-provenance.md` for the checkout snapshot that this skill matches.
