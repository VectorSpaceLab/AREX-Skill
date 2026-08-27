---
name: generation-and-api
description: "Use DALLE2-pytorch public generation and model APIs: DALLE2,
  diffusion prior, decoder, CLIP adapters, inpainting, latent diffusion/VQGAN,
  checkpoints, tokenizer, and dream CLI."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# generation-and-api

Use this sub-skill when the task is to construct or call DALLE2-pytorch public Python generation APIs, diagnose model/checkpoint generation failures, or use the installed `dream` console command for a trained DALL-E 2 checkpoint.

## Load This When

- Building `DALLE2`, `DiffusionPriorNetwork`, `DiffusionPrior`, `Unet`, or `Decoder` objects from Python.
- Choosing between `OpenAIClipAdapter`, `OpenClipAdapter`, package `CLIP`, precomputed embeddings, and trained checkpoints.
- Sampling with a prior, decoder, or chained `DALLE2` model, including `cond_scale` and `prior_cond_scale`.
- Debugging decoder inpainting, cascading decoder resolution order, latent diffusion with `VQGanVAE`, or tokenizer length issues.
- Checking that the installed `dalle2-pytorch` package can import or run a tiny CPU-safe forward-loss smoke test.

## Route Elsewhere

- JSON training launchers, config classes, trainer loops, Accelerate/DeepSpeed commands, checkpoint save/resume during training: `../training-and-configs/SKILL.md`.
- WebDataset, EmbeddingReader, shard layouts, experiment trackers, W&B/HuggingFace/S3 save/load configuration: `../data-and-tracking/SKILL.md`.

## Runtime Contract

- Public package: `pip install dalle2-pytorch`.
- Public import namespace: `import dalle2_pytorch`; top-level exports include `DALLE2`, `DiffusionPriorNetwork`, `DiffusionPrior`, `Unet`, `Decoder`, `OpenAIClipAdapter`, `OpenClipAdapter`, `DecoderTrainer`, `DiffusionPriorTrainer`, `VQGanVAE`, and `CLIP`.
- Version covered by this skill: `dalle2-pytorch` 1.15.6.
- Full text-to-image generation needs trained prior and decoder weights; realistic CLIP/decoder/prior sampling usually needs GPU memory. CPU is suitable for imports, CLI help, config checks, and tiny synthetic forward-loss smoke tests only.

## References And Bundled Script

- API signatures and object relationships: [references/api-reference.md](references/api-reference.md).
- Generation, tokenization, checkpoint, inpainting, and `dream` workflows: [references/workflows.md](references/workflows.md).
- Latent diffusion and VQGAN caveats: [references/latent-diffusion-and-vqgan.md](references/latent-diffusion-and-vqgan.md).
- Common failures and fixes: [references/troubleshooting.md](references/troubleshooting.md).
- Safe installed-package checker: [scripts/check_dalle2_runtime.py](scripts/check_dalle2_runtime.py).

## First Checks

```bash
python -m pip show dalle2-pytorch
python scripts/check_dalle2_runtime.py --mode imports
python scripts/check_dalle2_runtime.py --mode cli-help
```

For a CPU-only synthetic smoke test that does not download model weights:

```bash
python scripts/check_dalle2_runtime.py --mode tiny-forward
```

If any check fails, use [references/troubleshooting.md](references/troubleshooting.md) before escalating to training/config or data/tracking guidance.
