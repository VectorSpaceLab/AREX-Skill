---
name: janusflow-workflows
description: "Guides JanusFlow understanding and rectified-flow image generation
  with diffusers and an SDXL VAE."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# JanusFlow Workflows

Use this sub-skill when the task mentions JanusFlow, rectified flow, SDXL VAE, `image_gen_tag`, or the JanusFlow-1.3B model family.

## Read first

- [`references/janusflow-reference.md`](references/janusflow-reference.md) for the JanusFlow-specific API and flow-generation path.
- [`references/troubleshooting.md`](references/troubleshooting.md) for diffusers, VAE, and attention-mask failures.
- [`scripts/janusflow_text_to_image.py`](scripts/janusflow_text_to_image.py) for a safe dry-run helper and an optional real model run.

For installation and model-family selection, use the root [`../../references/installation-and-models.md`](../../references/installation-and-models.md).

## When to use this route

Choose this route when the user asks to:

- Generate images with JanusFlow-1.3B.
- Debug the rectified-flow loop, `image_gen_tag`, or VAE decode path.
- Adapt the JanusFlow demo.
- Compare JanusFlow with Janus / Janus-Pro understanding or generation.
- Investigate diffusers compatibility with the repository's torch wheel.

## Core workflow

1. Load the JanusFlow processor and model.
2. Load the SDXL VAE through diffusers.
3. Build a one-turn conversation and append `image_gen_tag`.
4. Tokenize the prompt and remove the last generation token before the flow loop.
5. Sample a latent `z` tensor and run the ODE-style update loop.
6. Decode the final latent through the vision decoder and VAE.
7. Save the resulting images.

## Dry-run before model execution

Validate the prompt and generation parameters without downloading weights:

```bash
python sub-skills/janusflow-workflows/scripts/janusflow_text_to_image.py \
  --model-id deepseek-ai/JanusFlow-1.3B \
  --prompt "A glass of red wine on a reflective surface."
```

The default mode prints a plan and does not download model weights. Add `--run-model` only after you confirm diffusers compatibility, CUDA, and SDXL VAE access.

## Route elsewhere

- Use [`../multimodal-understanding/SKILL.md`](../multimodal-understanding/SKILL.md) for JanusFlow understanding or image+question tasks.
- Use [`../image-generation/SKILL.md`](../image-generation/SKILL.md) for Janus / Janus-Pro autoregressive generation.
- Use [`../demos-and-serving/SKILL.md`](../demos-and-serving/SKILL.md) for Gradio or FastAPI serving.
