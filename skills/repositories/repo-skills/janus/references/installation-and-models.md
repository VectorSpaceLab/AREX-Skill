# Installation and Model Overview

## Purpose

Read this before using the Janus skill on a new machine or before choosing the right workflow branch. It summarizes the verified package shape, model families, and install variants that matter for common user tasks.

## Verified package facts

The repository declares the `janus` distribution and the source package exposes the public modules used by the skill:

- `janus.models`
- `janus.janusflow.models`
- `janus.utils.io`
- `janus.utils.conversation`

The public API used by the skill is centered on:

- `VLMImageProcessor`
- `VLChatProcessor`
- `MultiModalityCausalLM`
- `load_pil_images`

## Recommended install paths

### Base package

Use the editable install when working from a checkout:

```bash
pip install -e .
```

The repo metadata declares these runtime dependencies:

- `torch>=2.0.1`
- `transformers>=4.38.2`
- `timm>=0.9.16`
- `accelerate`
- `sentencepiece`
- `attrdict`
- `einops`

### Gradio demos

For the local demos, install the published extra:

```bash
pip install -e .[gradio]
```

The extra pulls in the demo UI and text utilities used by the Gradio apps.

### JanusFlow generation

JanusFlow adds a diffusion-style dependency surface. Use a diffusers build compatible with the installed torch wheel:

```bash
pip install diffusers[torch]
```

If the newest diffusers release raises import errors with the selected torch wheel, choose a compatible diffusers version instead. The verified inspection environment used `diffusers==0.30.3` with `torch==2.0.1`.

### Image-processing companion packages

The source package imports `torchvision` inside the image-processing path. Even though it is not declared in the project metadata, a working runtime environment should include it for the understanding workflows:

```bash
pip install torchvision
```

## Model families

### Janus

- Model ids documented in the repo: `deepseek-ai/Janus-1.3B`
- Core workflows:
  - multimodal understanding
  - autoregressive text-to-image generation
  - Gradio demo
  - FastAPI demo/service

### Janus-Pro

- Model ids documented in the repo: `deepseek-ai/Janus-Pro-1B`, `deepseek-ai/Janus-Pro-7B`
- Core workflows:
  - multimodal understanding
  - autoregressive text-to-image generation
  - Gradio demo

### JanusFlow

- Model id documented in the repo: `deepseek-ai/JanusFlow-1.3B`
- Core workflows:
  - multimodal understanding
  - rectified-flow text-to-image generation
  - Gradio demo

## When to choose which route

- Use **multimodal-understanding** when the task is about image+question prompts, OCR, formula conversion, or reading image content.
- Use **image-generation** when the task is about Janus or Janus-Pro text-to-image generation.
- Use **janusflow-workflows** when the task mentions JanusFlow, rectified flow, or SDXL VAE.
- Use **demos-and-serving** when the task is about Gradio or FastAPI.

## Public usage cautions

- The repo examples assume GPU execution for real generation; they are not good defaults for a CPU-only machine.
- The demos often load a model at import time. Prefer the generated skill's lazy-loading helpers when adapting them.
- The repo's README shows model download commands that require network access and Hugging Face model access.
- JanusFlow generation needs a diffusers build that matches the torch wheel. A newer diffusers release may fail even if installation succeeds.
