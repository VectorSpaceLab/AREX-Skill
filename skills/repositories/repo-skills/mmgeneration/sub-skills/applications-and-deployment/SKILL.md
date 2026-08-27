---
name: "applications-and-deployment"
description: "Guides MMGeneration latent editing, interpolation, projection,
  StyleCLIP, and TorchServe deployment workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Applications and Deployment

Use this sub-skill when the user wants to manipulate a StyleGAN-style latent space or package a model for serving.

## Typical triggers

- "How do I interpolate between two latent codes?"
- "How do I project an image into StyleGAN space?"
- "How do I run SeFa or StyleCLIP?"
- "How do I export a checkpoint for TorchServe?"
- "How do I explain the advanced app scripts?"

## Include here

- `apps/interpolate_sample.py`
- `apps/conditional_interpolate.py`
- `apps/stylegan_projector.py`
- `apps/modified_sefa.py`
- `apps/styleclip.py`
- `tools/deployment/mmgen2torchserver.py`
- `tools/deployment/mmgen_unconditional_handler.py`
- `tools/deployment/test_torchserver.py`
- StyleGAN latent-space assumptions and TorchServe packaging behavior

## Exclude here

- Basic sampling and translation -> `inference-and-sampling`
- Training and resume behavior -> `training-and-distribution`
- Metric evaluation -> `evaluation-and-metrics`
- Config and registry editing -> `configuration-and-extension`

## Read these files first

- `references/workflows.md`
- `references/troubleshooting.md`
- `../../references/model-overview.md`
- `../../references/api-reference.md`
- `../../references/cli-reference.md`

## What good guidance looks like

A future agent should be able to:

1. Tell the user which latent space or model family the script assumes.
2. Explain which apps need a StyleGAN-family generator versus a translation model.
3. Distinguish safe help/shape checks from expensive image-generation runs.
4. Describe the TorchServe packaging workflow without starting the server.
5. Warn about optional dependencies such as CLIP.

## Common failure modes

- The checkpoint is not StyleGAN-like, so the latent projection or SeFa route does not apply.
- The script expects `w` or `w+` latents, but the caller passes a different representation.
- StyleCLIP fails because the optional `clip` dependency is missing.
- TorchServe packaging fails because the external archiver/service is not installed.

For concrete recovery steps, read `references/troubleshooting.md`.
