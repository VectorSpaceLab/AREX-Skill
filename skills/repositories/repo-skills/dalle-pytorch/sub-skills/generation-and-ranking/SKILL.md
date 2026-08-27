---
name: generation-and-ranking
description: "Generate images or text with DALLE-pytorch checkpoints, prime with
  image tokens, and rank generations with CLIP."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Generation and ranking

Use this sub-skill when the user asks to generate images from text, generate text completions, split multiple prompts, inspect generation checkpoint compatibility, prime with an image crop, or use CLIP to rank generated images.

## Read first

- `references/workflows.md` for generation CLI/API recipes, prompt/output layout, `cond_scale`, image priming, and CLIP ranking.
- `references/troubleshooting.md` for checkpoint/VAE mismatches, CUDA-only helper behavior, text generation caveats, and output path issues.
- `scripts/build_generate_command.py` to produce a shell-safe command template for the historical helper surface.
- `scripts/tiny_generation_api_smoke.py` for a no-checkpoint API smoke.

## Typical routes

| Request | Action |
| --- | --- |
| "Generate images from a trained checkpoint" | Check checkpoint/VAE compatibility, build a command template, and warn that the helper calls CUDA and writes output images. |
| "Use `generate_images` in code" | Use the API recipe and tiny smoke; no source checkout is required. |
| "Generate multiple prompts" | Use pipe-separated prompts in the helper template or loop over tokenized prompts in API code. |
| "Rank samples with CLIP" | Build/bring a compatible `CLIP` scorer and use `DALLE.generate_images(text, clip=clip)` returning `(images, scores)`. |
| "Text completion with DALL-E" | Use `generate_texts`, but note source code creates CUDA tensors internally. |

## Boundary notes

- Creating VAE checkpoints belongs to `../vae-training/SKILL.md`.
- Creating/resuming DALL-E checkpoints belongs to `../dalle-training/SKILL.md`.
- CUDA/DeepSpeed/Horovod/Docker setup belongs to `../distributed-and-backends/SKILL.md`.

## Validation checklist

- DALL-E checkpoint has `hparams`, `weights`, `vae_params`, and a compatible `vae_class_name`.
- Tokenizer choice at generation matches training.
- `--taming` and VQGAN paths are used only when the checkpoint was trained with VQGAN.
- User approved output directory writes and GPU use.
- `top_k`, `batch_size`, and `num_images` are chosen to fit memory.
